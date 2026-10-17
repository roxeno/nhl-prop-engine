from datetime import date
from pathlib import Path

import pandas as pd
import numpy as np

import argparse
import sys

# ==========================================
# 1. GLOBAL CONSTANTS & FILE SETUP
# ==========================================

#../data/raw/skaters/filename
filename = sys.argv[1]

#today date
TODAY_STR = date.today().strftime("%Y-%m-%d")

#K tuning ; Tuning based on gamesplayed; Early season trust career; Late season trust season stats
K = 10  # shrinkage constant; higher = trust career more

#outputfile
output_dir_skater = Path("../data/trimmedSkaters/")
output_dir_defender = Path("../data/trimmedDefenders/")
output_dir_built = Path('../data/playingToday')

#careerfile path
career_file_skater = pd.read_csv("../data/raw/skaters/Career_hockeyskater.csv")


#seasonfile path
season_file_skater = pd.read_csv("../data/raw/skaters/Season_hockeyskater.csv")
season_file_defender = pd.read_csv("../data/raw/defenders/Defender_hockeyskater.csv")

#get schedule
schedulefile = f"../data/playingToday/games_{TODAY_STR}.csv"
get_tonightGames = pd.read_csv(schedulefile)
    

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================

def execute_trimskaters():
    df = season_file_skater
    
    desired_extracted_name = "TrimmedSeason_hockeyskater.csv"
    
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = df[df['situation'] == 'all']
    df = df.groupby(['playerId','name','team','games_played'])[['icetime','I_F_shotsOnGoal','I_F_missedShots']].sum().reset_index()

    df['shots_per_60'] = df['I_F_shotsOnGoal'] / (df['icetime'] / 3600)
    df['fenwick_per_60'] = (df['I_F_shotsOnGoal'] + df['I_F_missedShots']) / (df['icetime'] / 3600)
    
    df = pd.merge(df, career_file_skater, on='playerId', how='inner')

    df['season_weight'] = df['games_played'] / (df['games_played'] + K)
    df['career_weight'] = 1 - df['season_weight']

    df['playerweighted_shotsper60'] = (
    df['season_weight'] * df['shots_per_60'] +
    df['career_weight'] * df['career_shots_per_60'])

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
    

def execute_trimdefenders():  
    df = season_file_defender
    career_file_defender = pd.read_csv("../data/raw/defenders/C_Defender_hockeyskater.csv")

    desired_extracted_name = "TrimmedSeason_hockeydefender.csv"
    
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = pd.merge(df, career_file_defender, on='team', how='inner')

    df = df.rename(columns={'team' : 'opponent'})
    final_destination = output_dir_defender / desired_extracted_name
    df.to_csv(final_destination, index=False)

def execute_commenceGameNight():
    #trimmed path
    trimmed_file_skater = pd.read_csv('../data/trimmedSkaters/TrimmedSeason_hockeyskater.csv')
    trimmed_file_defender = pd.read_csv('../data/trimmedDefenders/TrimmedSeason_hockeydefender.csv')

    desired_extracted_name = "tonightGame.csv"
    dfB = trimmed_file_defender
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = pd.merge(trimmed_file_skater, get_tonightGames, on='team', how='inner')
    df = pd.merge(df, dfB, on='opponent', how='inner')

    df = df[['playerId','name','team','home_or_away','shots_per_60','fenwick_per_60','career_shots_per_60','opponent','team_xGA_per_60','Career_team_xGA_per_60','leagueAvgXGAper60','blendedavgtoimin']]

    final_destination = output_dir_built / desired_extracted_name

    df.to_csv(final_destination, index=False)

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
        choices=["trimS", "trimCD", "trimD", "gametime", "all"],
        help=(
            "trimS   : trim skater file"
            "trimCD   : trim defender file"
            "trimD   : trim defender file"
            "gametime : gamenight schedule"
            "all     : Execute all 3 jobs sequentially"
        )
    )

    args = parser.parse_args()

    if args.action == "trimS":
        execute_trimskaters()
    elif args.action == "trimCD":
        execute_trimcareer()
    elif args.action == "trimD":
        execute_trimdefenders()
    elif args.action == "gametime":
        execute_commenceGameNight()
    elif args.action == "all":
        print("Executing comprehensive batch sequence...")
        execute_trimskaters()
        execute_trimdefenders()
        execute_commenceGameNight()

   


if __name__ == "__main__":
    main()