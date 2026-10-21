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
K = 10  # shrinkage constant; higher = trust career more
LEAGUE_AVG_HD_RATIO = 0.18

#outputfile
output_dir_skater = Path("../data/trimmedSkaters/")
output_dir_defender = Path("../data/trimmedDefenders/")
output_dir_built = Path('../data/playingToday')

#careerfile path
career_file_skater = pd.read_csv("../data/raw/skaters/Career_hockeyskater.csv")


#seasonfile path
season_file_skater = pd.read_csv("../data/raw/skaters/Season_hockeyskater.csv")
season_file_defender = pd.read_csv("../data/raw/defenders/Defender_hockeyskater.csv")

#goalie path
#goalie_file = pd.read_csv(f"../data/playingToday/goalie_{TODAY_STR}.csv")
goalie_file = pd.read_csv(f"../data/playingToday/goalie_2026-10-20.csv")

#get schedule
#get_tonightGames = pd.read_csv(f"../data/playingToday/games_{TODAY_STR}.csv")
get_tonightGames = pd.read_csv(f"../data/playingToday/games_2026-10-20.csv")
get_yesterdayGame = pd.read_csv(f"../data/playingToday/games_{YESTERDAY_STR}.csv")
    

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================



def execute_trimskaters():
    df = season_file_skater
    desired_extracted_name = "TrimmedSeason_hockeyskater.csv"
    
    # 1. Original 'all' logic
    df = df[df['situation'] == 'all']
    df = df.groupby(['playerId','name','team','games_played'])[['icetime','I_F_shotsOnGoal','I_F_missedShots','I_F_highDangerShots','I_F_shotAttempts']].sum().reset_index()

    # 2. Calculate Rates
    df['shots_per_60'] = df['I_F_shotsOnGoal'] / (df['icetime'] / 3600)
    df['fenwick_per_60'] = (df['I_F_shotsOnGoal'] + df['I_F_missedShots']) / (df['icetime'] / 3600)
    
    # 🚨 NEW: HD Ratio (What % of their shots are high-danger?)
    # We add 0.001 to prevent division by zero for players with 0 shots
    df['raw_hd_ratio'] = df['I_F_highDangerShots'] / (df['I_F_shotAttempts'] + 0.001)
    
    # 3. The New PP Logic
    df_pp = season_file_skater[season_file_skater['situation'] == '5on4']
    df_pp = df_pp.groupby(['playerId','games_played'])[['icetime', 'I_F_shotsOnGoal','I_F_highDangerShots']].sum().reset_index()
    df_pp['5on4_shots_per_60'] = df_pp['I_F_shotsOnGoal'] / (df_pp['icetime'] / 3600)
    df_pp['5on4_avg_toi_min'] = (df_pp['icetime'] / df_pp['games_played']) / 60
    df_pp['5on4_hd_ratio'] = df_pp['I_F_highDangerShots'] / (df_pp['I_F_shotsOnGoal'] + 0.001)
    
    # Keep only the PP columns to merge
    df_pp = df_pp[['playerId', '5on4_shots_per_60', '5on4_avg_toi_min', '5on4_hd_ratio']]
    
    # 4. Merge the PP stats into the main df
    df = pd.merge(df, df_pp, on='playerId', how='left')
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].fillna(0)
    df['5on4_hd_ratio'] = df['5on4_hd_ratio'].fillna(0)
    df['5on4_avg_toi_min'] = df['5on4_avg_toi_min'].fillna(0)
    
    # 5. Merge Career
    df = pd.merge(df, career_file_skater, on='playerId', how='inner')

    # 6. Blending (Total Shots)
    df['season_weight'] = df['games_played'] / (df['games_played'] + K)
    df['career_weight'] = 1 - df['season_weight']

    df['hd_ratio'] = (df['season_weight'] * df['raw_hd_ratio']) + (df['career_weight'] * LEAGUE_AVG_HD_RATIO)

    df['playerweighted_shotsper60'] = (
        df['season_weight'] * df['shots_per_60'] +
        df['career_weight'] * df['career_shots_per_60']
    )
    

    # 7. Blending (TOI)
    df['season_avg_toi_sec'] = df['icetime'] / df['games_played']
    df['blendedavgtoimin'] = ((0.6 * df['season_avg_toi_sec']) + (0.4 * df['career_icetime'])) / 60

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
        'playerId', 'name', 'team', 'home_or_away', 'opponent',
        'shots_per_60', 'hd_ratio', 'fenwick_per_60', 'career_shots_per_60', 
        '5on4_shots_per_60', '5on4_hd_ratio' ,'5on4_avg_toi_min', 
        'team_xGA_per_60', 'Career_team_xGA_per_60', 'leagueAvgXGAper60', 'sv_pct',
        'blendedavgtoimin','player_team_b2b', 'opponent_b2b'
    ]]
    """if file_to_delete.exists():
        os.remove(file_to_delete)
        print(f"🗑️ Deleted old schedule: {file_to_delete.name}")
    else:
        print(f"✅ No schedule found to delete for {YESTERDAY_STR}.")"""


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