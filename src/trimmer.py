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

#outputfile
output_dir_skater = Path("../data/trimmedSkaters/")
output_dir_defender = Path("../data/trimmedDefenders/")
output_dir_built = Path('../data/playingToday')

#careerfile path
career_file_skater = pd.read_csv("../data/raw/skaters/Career_hockeyskater.csv")
career_file_defender = pd.read_csv("../data/raw/defenders/Career_hockeyTeam_defensive.csv")

#trimmed path
trimmed_file_skater = pd.read_csv('../data/trimmedSkaters/TrimmedSeason_hockeyskater.csv')
trimmed_file_defender = pd.read_csv('../data/trimmedDefenders/TrimmedSeason_hockeydefender.csv')

#get schedule
get_tonightGames = pd.read_csv('../data/playingToday/games_2026-10-15.csv')
    

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================

def execute_trimskaters():
    df = pd.read_csv(filename)
    
    desired_extracted_name = "TrimmedSeason_hockeyskater.csv"
    
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    df = df[df['situation'] == 'all']
    
    df = df.groupby(['playerId','name','playerTeam'])[['icetime','I_F_shotsOnGoal','I_F_missedShots']].sum().reset_index()

    df['shots_per_60'] = df['I_F_shotsOnGoal'] / (df['icetime'] / 3600)
    df['fenwick_per_60'] = (df['I_F_shotsOnGoal'] + df['I_F_missedShots']) / (df['icetime'] / 3600)

    df = df[['playerId','name','playerTeam','shots_per_60','fenwick_per_60']]
    df = pd.merge(df, career_file_skater, on='playerId', how='inner')

    final_destination = output_dir_skater / desired_extracted_name
    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"
    counter = 1

    # Loop to increment the filename if it already exists
    while final_destination.exists():
        final_destination = output_dir_skater / f"{base_name}-{counter}{extension}"
        counter += 1
    df.to_csv(final_destination, index=False)

def execute_trimdefenders():
    df = pd.read_csv(filename)
    
    desired_extracted_name = "TrimmedSeason_hockeydefender.csv"
    
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = pd.merge(df, career_file_defender, on='playerTeam', how='inner')
    df = df[['playerTeam','blockedShotsPer60','careerblockedShotsPer60']]

    final_destination = output_dir_defender / desired_extracted_name
    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"
    counter = 1

    # Loop to increment the filename if it already exists
    while final_destination.exists():
        final_destination = output_dir_defender / f"{base_name}-{counter}{extension}"
        counter += 1
    df.to_csv(final_destination, index=False)

def execute_commenceGameNight():
    desired_extracted_name = "tonightGame.csv"
    dfB = trimmed_file_defender
    #filtering the data to only include few stuff
    #,'playerTeam' fenwick
    
    df = pd.merge(trimmed_file_skater, get_tonightGames, on='playerTeam', how='inner')
    dfB = dfB.rename(columns={'playerTeam':'opponent'})
    df = pd.merge(df, dfB, on='opponent', how='inner')

    df = df[['playerId','name','playerTeam','home_or_away','shots_per_60','fenwick_per_60','career_shots_per_60','opponent','blockedShotsPer60','careerblockedShotsPer60']]

    final_destination = output_dir_built / desired_extracted_name

    df.to_csv(final_destination, index=False)

# ==========================================
# 3. THE INTERACTIVE CONTROL ROOM
# ==========================================
def main():
    parser = argparse.ArgumentParser(
        prog="python -m code",
        description="NHL stats pipeline: trim skaters, trim defenders, or prep game night."
    )
    sub = parser.add_subparsers(dest="action", required=True)

    # --- trimS ---
    p_s = sub.add_parser("trimS", help="Trim NHL skaters and add career stats")
    p_s.add_argument("file", type=str, help="Path to input skaters CSV")

    # --- trimD ---
    p_d = sub.add_parser("trimD", help="Trim NHL defenders and add career stats")
    p_d.add_argument("file", type=str, help="Path to input defenders CSV")

    # --- gametime ---
    sub.add_parser("gametime", help="Prep tonight's games (no file needed)")

    args = parser.parse_args()

    # --- dispatch ---
    if args.action == "trimS":
        execute_trimskaters(args.file)
    elif args.action == "trimD":
        execute_trimdefenders(args.file)
    elif args.action == "gametime":
        execute_commenceGameNight()


if __name__ == "__main__":
    main()