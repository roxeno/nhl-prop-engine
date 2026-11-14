from datetime import date
from pathlib import Path
from scraper import get_yesterday_str,get_b2b_teams_from_storage
import pandas as pd
import numpy as np

import argparse
import sys
import os

# ==========================================
# 1. GLOBAL CONSTANTS & FILE SETUP
# ==========================================


#today date
TODAY_STR = date.today().strftime("%Y-%m-%d")
YESTERDAY_STR = get_yesterday_str()

#Directory
target_directory = Path("../data/playingToday")

#K tuning ; Tuning based on gamesplayed; Early season trust career; Late season trust season stats
K_SEASON = 6  # lower → trust current season sooner
K_CAREER = 25   # higher → down-weight 1-year careers

#outputfile
output_dir_skater = Path("../data/trimmedSkaters/")
output_dir_defender = Path("../data/trimmedDefenders/")
output_dir_built = Path('../data/playingToday')

#careerfile path
career_file_skater = pd.read_csv("../assets/Careerprior_hockeyskater.csv")


#seasonfile path
season_file_skater = pd.read_csv("../data/raw/skaters/Season_hockeyskater.csv")
season_file_defender = pd.read_csv("../data/raw/defenders/Defender_hockeyskater.csv")



    

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================
def execute_trimskaters():
    df = season_file_skater
    desired_extracted_name = "TrimmedSeason_hockeyskater.csv"
    
    # 1. Original 'all' logic
    df = df[df['situation'].isin(['5on5', '5on4', '4on5'])]
    df = df.groupby(['playerId','name','team','games_played'])[['icetime','I_F_shotsOnGoal','I_F_missedShots','I_F_highDangerShots','I_F_goals','I_F_highDangerGoals']].sum().reset_index()

    # 2. Compute league averages ONCE (used for three-way blend)
    LEAGUE_HD_PER_60 = (
        df['I_F_highDangerShots'].sum() / (df['icetime'].sum() / 3600.0)
    ).round(2)
    LEAGUE_SHOTS_PER_60 = (
        df['I_F_shotsOnGoal'].sum() / (df['icetime'].sum() / 3600.0)
    ).round(2)
    LEAGUE_HD_SH_PCT = (
        sum(df['I_F_highDangerGoals']) / sum(df['I_F_highDangerShots'])
    )
    career_non_hd_goals = sum(df['I_F_goals']) - sum(df['I_F_highDangerGoals'])
    career_non_hd_shots = sum(df['I_F_shotsOnGoal']) - sum(df['I_F_highDangerShots'])
    LEAGUE_NON_HD_SH_PCT = career_non_hd_goals / career_non_hd_shots

    LEAGUE_TOI_SEC = 900
    
    # 3. Calculate Rates — NO placeholder override; let the blend shrink zeros
    df['shots_per_60'] = df['I_F_shotsOnGoal'] / (df['icetime'] / 3600)
    df['fenwick_per_60'] = (df['I_F_shotsOnGoal'] + df['I_F_missedShots']) / (df['icetime'] / 3600)
    df['hd_shots_per_60'] = df['I_F_highDangerShots'] / (df['icetime'] / 3600)
    df['non_hd_goals'] = df['I_F_goals'] - df['I_F_highDangerGoals']
    df['non_hd_shots'] = df['I_F_shotsOnGoal'] - df['I_F_highDangerShots']
    df['hd_sh_pct'] = (df['I_F_highDangerGoals'] / df['I_F_highDangerShots'].replace(0, np.nan)).fillna(LEAGUE_HD_PER_60).clip(0.00, 0.50)
    df['non_hd_sh_pct'] = (df['non_hd_goals'] / df['non_hd_shots'].replace(0, np.nan)).fillna(LEAGUE_NON_HD_SH_PCT).clip(0.00, 0.30)
    # 4. The New PP Logic (per-player PP rates)
    df_pp = season_file_skater[season_file_skater['situation'] == '5on4']
    df_pp = df_pp.groupby(['playerId','games_played'])[
        ['icetime', 'I_F_shotsOnGoal','I_F_highDangerShots']
    ].sum().reset_index()

    df_pp['5on4_shots_per_60'] = df_pp['I_F_shotsOnGoal'] / (df_pp['icetime'] / 3600)
    df_pp['5on4_avg_toi_min']  = (df_pp['icetime'] / df_pp['games_played']) / 60
    target_pp_toi = 2.5   # was 2.0

    current_mean = df_pp['5on4_avg_toi_min'].mean()
    if current_mean > 0.1:
        scale = 2.5 / current_mean
        df_pp['5on4_avg_toi_min'] = df_pp['5on4_avg_toi_min'] * scale
        print(f"PP TOI scaled: {current_mean:.2f} → {df_pp['5on4_avg_toi_min'].mean():.2f}")
    else:
        print(f"⚠️  Skipping PP TOI scale — current mean is {current_mean:.2f}")


    # League PP rate — computed from raw df_pp BEFORE merging in zeros

    print("df_pp shape:", df_pp.shape)
    print("Unique playerIds:", df_pp['playerId'].nunique())
    print("Total rows:", len(df_pp))
    LEAGUE_PP_SHOTS_PER_60 = 5
    print(f"LEAGUE_PP_SHOTS_PER_60: {LEAGUE_PP_SHOTS_PER_60:.2f}")

    # In df_pp (before merging), compute PP games played:
    df_pp['pp_games'] = df_pp['icetime'] / (df_pp['5on4_avg_toi_min'] * 60)
    # Careful: 5on4_avg_toi_min was already computed from icetime/games_played,
    # so pp_games === games_played in df_pp. Use that directly instead.

    # Cleaner: use df_pp['games_played'] directly as PP games proxy.
    # (Only an approximation — a player may have played 15 games but zero PP — but
    # for players who DO have PP time, this is close enough.)

    PP_PRIOR_MIN = 20  # minutes of league-average PP rate as prior
    df_pp['pp_trust'] = (df_pp['icetime'] / 60) / ((df_pp['icetime'] / 60) + PP_PRIOR_MIN)

    # 5. Merge the PP stats into the main df
    df = pd.merge(df, df_pp[['playerId','5on4_shots_per_60','5on4_avg_toi_min','pp_trust']],
              on='playerId', how='left')
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].fillna(0)
    df['5on4_avg_toi_min']  = df['5on4_avg_toi_min'].fillna(0)
    df['pp_trust']          = df['pp_trust'].fillna(0)

    # Apply sample-size-dependent shrinkage
    df['5on4_shots_per_60'] = np.where(
        df['5on4_avg_toi_min'] > 0,
        df['pp_trust'] * df['5on4_shots_per_60'] + (1 - df['pp_trust']) * LEAGUE_PP_SHOTS_PER_60,
        0.0
    )
    

    # Hard cap: no player realistically shoots above ~20 per 60 on the PP
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].clip(upper=20)
    
    # 7. Load and merge the prior-year career priors
    df = pd.merge(df, career_file_skater[['playerId', 'career_hd_per_60','career_shots_per_60','career_icetime','career_games','career_non_hd_goals','career_non_hd_shots','career_hd_sh_pct','career_non_hd_sh_pct']], on='playerId', how='left')
    
    # --- Guards: missing career data → fall back to league average (fillna only, NOT == 0) ---
    df['career_hd_per_60'] = df['career_hd_per_60'].fillna(LEAGUE_HD_PER_60)
    df['career_shots_per_60'] = df['career_shots_per_60'].fillna(LEAGUE_SHOTS_PER_60)
    df['career_hd_sh_pct'] = df['career_hd_sh_pct'].fillna(LEAGUE_HD_SH_PCT)
    df['career_non_hd_sh_pct'] = df['career_non_hd_sh_pct'].fillna(LEAGUE_NON_HD_SH_PCT)
    df['career_icetime'] = df['career_icetime'].fillna(df['icetime'])
    df['career_games'] = df['career_games'].fillna(df['games_played'])
    

    # 8. THREE-WAY BLENDING (season / career / league average)
    # Season trust: GP-based
    df['season_weight'] = df['games_played'] / (df['games_played'] + K_SEASON)

    # Career trust: also GP-based (down-weight small career samples)
    career_trust = df['career_games'] / (df['career_games'] + K_CAREER)

    # Effective weights
    df['career_weight'] = (1 - df['season_weight']) * career_trust
    df['league_weight'] = 1 - df['season_weight'] - df['career_weight']

    # After computing season_weight and career_weight:
# For high-volume shooters, trust the current season more

    # Identify high-volume shooters by their raw season rate
    high_volume = df['shots_per_60'] > 9.0

    # For them, inflate season_weight and deflate career_weight
    df['season_weight_adj'] = np.where(
        high_volume,
        df['season_weight'] + 0.15,   # bump season weight by 15%
        df['season_weight']
    )
    # Clip so it doesn't exceed 0.85
    df['season_weight_adj'] = df['season_weight_adj'].clip(upper=0.85)

    # Recompute career_weight and league_weight with adjusted season weight
    df['career_weight_adj'] = (1 - df['season_weight_adj']) * (
        df['career_games'] / (df['career_games'] + K_CAREER)
    )
    df['league_weight_adj'] = 1 - df['season_weight_adj'] - df['career_weight_adj']

    # Recompute the blend with adjusted weights
    df['blended_shots_per60'] = (
        df['season_weight_adj'] * df['shots_per_60']
        + df['career_weight_adj'] * df['career_shots_per_60']
        + df['league_weight_adj'] * LEAGUE_SHOTS_PER_60
    )

    # Blend HD Shots
    df['blended_hd_per_60'] = (
        df['season_weight'] * df['hd_shots_per_60']
        + df['career_weight'] * df['career_hd_per_60']
        + df['league_weight'] * LEAGUE_HD_PER_60
    )

    # Blend hd_sh_pct
    df['blended_hd_pct'] = (
            df['season_weight'] * df['hd_sh_pct']
            + df['career_weight'] * df['career_hd_sh_pct']
            + df['league_weight'] * LEAGUE_HD_SH_PCT
        )

    # Blend non_hd_sh_pct
    df['blended_non_hd_pct'] = (
            df['season_weight'] * df['non_hd_sh_pct']
            + df['career_weight'] * df['career_non_hd_sh_pct']
            + df['league_weight'] * LEAGUE_NON_HD_SH_PCT
        )

    # Blend TOI (same three-way)
    df['season_avg_toi_sec'] = df['icetime'] / df['games_played']
    df['career_avg_toi_sec'] = df['career_icetime'] / df['career_games']
    df['blendedavgtoimin'] = (
        df['season_weight'] * df['season_avg_toi_sec']
        + df['career_weight'] * df['career_avg_toi_sec']
        + df['league_weight'] * LEAGUE_TOI_SEC
    ) / 60
    print("blendedavgtoimin mean:", df['blendedavgtoimin'].mean())
    print("season_avg_toi_sec mean:", df['season_avg_toi_sec'].mean())
    print("5on4_shots_per_60 mean:", df['5on4_shots_per_60'].mean())

    final_destination = output_dir_skater / desired_extracted_name
    df.to_csv(final_destination, index=False)


def execute_trimcareer():
    df = pd.read_csv('../assets/skaters.csv')
    df = df[df['situation'] == 'all']
    
    # Build the team defense metric
    df = df.groupby('team').agg(
            total_icetime=('icetime', 'sum'),
            total_xga=('OnIce_A_xGoals', 'sum')
        ).reset_index()

    df['Career_team_xGA_per_60'] = df['total_xga'] / (df['total_icetime'] / 3600)
    
    df = df[['team', 'Career_team_xGA_per_60']]

    df.to_csv("../data/raw/defenders/C_Defender_hockeyskater.csv", index=False, encoding="utf-8")
    

def execute_opponent():  
    goalie_file = pd.read_csv(f"../data/playingToday/goalie_{TODAY_STR}.csv")

    df = season_file_defender
    career_file_defender = pd.read_csv("../data/raw/defenders/C_Defender_hockeyskater.csv")

    desired_extracted_name = "TrimmedSeason_hockeydefender.csv"
    
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = pd.merge(df, career_file_defender, on='team', how='inner')
    df = pd.merge(df,goalie_file, on='team',how='inner')

    df = df.rename(columns={'team' : 'opponent'})
    df['sv_pct'] = pd.to_numeric(df['sv_pct'], errors='coerce')
    df['sv_pct'] = df['sv_pct'].fillna(0.905)
    final_destination = output_dir_defender / desired_extracted_name
    df.to_csv(final_destination, index=False)

def execute_commenceGameNight():
    #load yesterday game schedule
    get_tonightGames = pd.read_csv(f"../data/playingToday/games_{TODAY_STR}.csv")
    get_yesterdayGame = pd.read_csv(f"../data/playingToday/games_{YESTERDAY_STR}.csv")

    b2b_teams = get_yesterdayGame

    # Load trimmed data
    trimmed_file_skater = pd.read_csv('../data/trimmedSkaters/TrimmedSeason_hockeyskater.csv')
    trimmed_file_defender = pd.read_csv('../data/trimmedDefenders/TrimmedSeason_hockeydefender.csv')

    desired_extracted_name = "tonightGame.csv"
    dfB = trimmed_file_defender
    
    # 1. Merge Skaters with Tonight's Schedule
    df = pd.merge(trimmed_file_skater, get_tonightGames, on='team', how='inner')
    
    # 2. Merge with Opponent Defensive Stats
    df = pd.merge(df, dfB, on='opponent', how='inner')

    #3.
    b2b_teams = get_b2b_teams_from_storage()
    # Create boolean flags (1 if true, 0 if false)
    df['player_team_b2b'] = df['team'].isin(b2b_teams).astype(int)
    df['opponent_b2b'] = df['opponent'].isin(b2b_teams).astype(int)
    
    # 4. Keep ONLY the necessary columns
    # INCLUDING the new 5on4 PP columns we just built!
    df = df[[
    'playerId', 'name', 'team', 'home_or_away', 'opponent', 'games_played', 'career_games',
    'shots_per_60', 'hd_shots_per_60', 'fenwick_per_60', 'career_shots_per_60', 
    '5on4_shots_per_60' ,'5on4_avg_toi_min', 'I_F_highDangerShots', 'icetime',
    'team_xGA_per_60', 'Career_team_xGA_per_60', 'leagueAvgXGAper60', 'sv_pct',
    'blendedavgtoimin', 'blended_hd_per_60','player_team_b2b', 'opponent_b2b','blended_shots_per60','blended_hd_pct', 'blended_non_hd_pct'
    ]]

    df = df.sort_values('blendedavgtoimin', ascending=False)
    df = df.drop_duplicates(subset=['playerId'], keep='first')


    final_destination = output_dir_built / desired_extracted_name
    df.to_csv(final_destination, index=False)
    print(f"Successfully built GameNight file at {final_destination}")

# ==========================================
# 3. THE INTERACTIVE CONTROL ROOM
# ==========================================
def main():
    parser = argparse.ArgumentParser(
            description="Unified Data Utility Platform",
            formatter_class=argparse.RawTextHelpFormatter
    )
    

    # Add your command line choice argument mapping directly to your functions
    parser.add_argument(
        "action",
        choices=["trimS", "trimCD", "trimO", "gametime", "all"],
        help=(
            "trimS   : trim skater file"
            "trimCD   : trim defender file"
            "trimO   : trim opponent file"
            "gametime : gamenight schedule"
            "all     : Execute all 3 jobs sequentially"
        )
    )

    args = parser.parse_args()

    if args.action == "trimS":
        execute_trimskaters()
    elif args.action == "trimCD":
        execute_trimcareer()
    elif args.action == "trimO":
        execute_opponent()
    elif args.action == "gametime":
        execute_commenceGameNight()
    elif args.action == "all":
        print("Executing comprehensive batch sequence...")
        execute_trimcareer()
        execute_trimskaters()
        execute_opponent()
        execute_commenceGameNight()

   


if __name__ == "__main__":
    main()