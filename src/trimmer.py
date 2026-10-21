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
K = 30  # shrinkage constant; higher = trust career more

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
    df = df[df['situation'] == 'all']
    df = df.groupby(['playerId','name','team','games_played'])[['icetime','I_F_shotsOnGoal','I_F_missedShots','I_F_highDangerShots','I_F_shotAttempts']].sum().reset_index()

    # 2. Compute league averages ONCE (used for three-way blend)
    LEAGUE_HD_PER_60 = (
        df['I_F_highDangerShots'].sum() / (df['icetime'].sum() / 3600.0)
    ).round(2)
    LEAGUE_SHOTS_PER_60 = (
        df['I_F_shotsOnGoal'].sum() / (df['icetime'].sum() / 3600.0)
    ).round(2)
    LEAGUE_TOI_SEC = 15 * 60  # ~15 min league average, adjust if you have real number

    # 3. Calculate Rates — NO placeholder override; let the blend shrink zeros
    df['shots_per_60'] = df['I_F_shotsOnGoal'] / (df['icetime'] / 3600)
    df['fenwick_per_60'] = (df['I_F_shotsOnGoal'] + df['I_F_missedShots']) / (df['icetime'] / 3600)
    df['hd_shots_per_60'] = df['I_F_highDangerShots'] / (df['icetime'] / 3600)
    
    # 4. The New PP Logic
    df_pp = season_file_skater[season_file_skater['situation'] == '5on4']
    df_pp = df_pp.groupby(['playerId','games_played'])[['icetime', 'I_F_shotsOnGoal','I_F_highDangerShots']].sum().reset_index()
    df_pp['5on4_shots_per_60'] = df_pp['I_F_shotsOnGoal'] / (df_pp['icetime'] / 3600)
    df_pp['5on4_avg_toi_min'] = (df_pp['icetime'] / df_pp['games_played']) / 60
    
    # Keep only the PP columns to merge
    df_pp = df_pp[['playerId', '5on4_shots_per_60', '5on4_avg_toi_min']]
    
    # 5. Merge the PP stats into the main df
    df = pd.merge(df, df_pp, on='playerId', how='left')
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].fillna(0)
    df['5on4_avg_toi_min'] = df['5on4_avg_toi_min'].fillna(0)
    
    # 6. Load and merge the prior-year career priors
    df = pd.merge(df, career_file_skater[['playerId', 'career_hd_per_60','career_shots_per_60','career_icetime','career_games']], on='playerId', how='left')
    
    # --- Guards: missing career data → fall back to league average (fillna only, NOT == 0) ---
    df['career_hd_per_60'] = df['career_hd_per_60'].fillna(LEAGUE_HD_PER_60)
    df['career_shots_per_60'] = df['career_shots_per_60'].fillna(LEAGUE_SHOTS_PER_60)
    df['career_icetime'] = df['career_icetime'].fillna(df['icetime'])
    df['career_games'] = df['career_games'].fillna(df['games_played'])

    # 7. THREE-WAY BLENDING (season / career / league average)
    # Season trust: GP-based
    df['season_weight'] = df['games_played'] / (df['games_played'] + K)

    # Career trust: also GP-based (down-weight small career samples)
    career_trust = df['career_games'] / (df['career_games'] + K)

    # Effective weights
    df['career_weight'] = (1 - df['season_weight']) * career_trust
    df['league_weight'] = 1 - df['season_weight'] - df['career_weight']

    # Blend Total Shots
    df['playerweighted_shotsper60'] = (
        df['season_weight'] * df['shots_per_60']
        + df['career_weight'] * df['career_shots_per_60']
        + df['league_weight'] * LEAGUE_SHOTS_PER_60
    )

    # Blend HD Shots
    df['blended_hd_per_60'] = (
        df['season_weight'] * df['hd_shots_per_60']
        + df['career_weight'] * df['career_hd_per_60']
        + df['league_weight'] * LEAGUE_HD_PER_60
    )

    # Blend TOI (same three-way)
    df['season_avg_toi_sec'] = df['icetime'] / df['games_played']
    df['career_avg_toi_sec'] = df['career_icetime'] / df['career_games']
    df['blendedavgtoimin'] = (
        df['season_weight'] * df['season_avg_toi_sec']
        + df['career_weight'] * df['career_avg_toi_sec']
        + df['league_weight'] * LEAGUE_TOI_SEC
    ) / 60

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
    final_destination = output_dir_defender / desired_extracted_name
    df.to_csv(final_destination, index=False)

def execute_commenceGameNight():
    #load yesterday game schedule
    get_tonightGames = pd.read_csv(f"../data/playingToday/games_{TODAY_STR}.csv")
    get_yesterdayGame = pd.read_csv(f"../data/playingToday/games_{YESTERDAY_STR}.csv")
    file_to_delete = target_directory / f"games_{YESTERDAY_STR}.csv"
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
    'blendedavgtoimin', 'blended_hd_per_60','player_team_b2b', 'opponent_b2b'
    ]]


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