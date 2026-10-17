from datetime import date,datetime,timedelta
from pathlib import Path

import pandas as pd

import requests
import argparse
import zipfile

import csv
import sys
import os


# ==========================================
# 1. GLOBAL CONSTANTS & FILE SETUP
# ==========================================
DOWNLOAD_DIR = Path("../data")
DOWNLOAD_DIR.mkdir(exist_ok=True)  # Ensures the folder exists

TODAY_STR = date.today().strftime("%Y-%m-%d")

def get_yesterday_str():
    """Returns yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

target_folder_skater = DOWNLOAD_DIR/'raw/skaters'
target_folder_defender = DOWNLOAD_DIR/'raw/defenders'

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================


import pandas as pd

def execute_skater_season():
    """Engine 1: Downloads a compressed zip for skaters and extracts it locally."""
    print(f"[{TODAY_STR}] Running Zip Extraction Utility...")
    
    url = 'https://moneypuck.com/moneypuck/playerData/seasonSummary/2026/regular/skaters.csv'
    final_destination_skater = target_folder_skater / "Season_hockeyskater.csv"
    final_destination_defender = target_folder_defender / "Defender_hockeyskater.csv"
    
    print("Fetching live data from moneypuck...")
    
    df = pd.read_csv(url)
    
    # FIX 2: Filter to 'all' situations so we don't double-count events
    df_all = df[df['situation'] == 'all']

    # Build the team defense metric
    df_def = df_all.groupby('team').agg(
        total_icetime=('icetime', 'sum'),
        total_xga=('OnIce_A_xGoals', 'sum')
    ).reset_index()
    
    df_def['team_xGA_per_60'] = df_def['total_xga'] / (df_def['total_icetime'] / 3600)

    league_avg = df_def["team_xGA_per_60"].mean()
    df_def["leagueAvgXGAper60"] = league_avg
    # Save both files
    df.to_csv(final_destination_skater, index=False, encoding="utf-8")
    
    # Just save the 3 clean columns for the analyzer
    df_def = df_def[['team', 'team_xGA_per_60','leagueAvgXGAper60']]
    df_def.to_csv(final_destination_defender, index=False, encoding="utf-8")

    print("Download complete")

def execute_skater_career():
    """Engine 2: Downloads data and processes it using standard built-in csv."""
    print(f"[{TODAY_STR}] Running Raw CSV Streams...")
    # Example placeholder behavior using the native 'csv' module
    
    #Target NHL Stats API URL
    start = 0
    limit= 100

    desired_extracted_name = "Career_hockeyskater.csv"

    
    all_df = []

    print("Fetching live data from NHL API...")
    for i in range(10):
        NHL_API_URL = f"https://api.nhle.com/stats/rest/en/skater/summary?isAggregate=true&isGame=false&sort=%5B%7B%22property%22:%22shots%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22playerId%22,%22direction%22:%22ASC%22%7D%5D&start={start}&limit={limit}&cayenneExp=active%3D1%20and%20gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=19171918"
        response = requests.get(NHL_API_URL,timeout=20)
        response.raise_for_status()

        json_payload = response.json()
    
        all_df.append(pd.DataFrame(json_payload.get("data",[])))

        start +=100

    df = pd.concat(all_df,ignore_index=True)
    #Only needed section
    df['career_shots_per_60'] = df['shots'] / df['gamesPlayed'] /df['timeOnIcePerGame'] * 3600
    df['career_toi'] = df['timeOnIcePerGame']
    df = df[['playerId','career_shots_per_60','career_toi']]
    
    final_destination = target_folder_skater / desired_extracted_name
    df.to_csv(final_destination, index=False, encoding="utf-8")
    print(f"Success! Saved {len(df)} players records into '{final_destination}'.")

    


def execute_today_schedule():
    """Engine 3: Downloads and flattens NHL schedule json into a CSV."""
    print(f"[{TODAY_STR}] Running NHL schedule Export...")
    yesterday_str = get_yesterday_str()
    url = f"https://api-web.nhle.com/v1/schedule/{TODAY_STR}"
    target_directory = DOWNLOAD_DIR/ 'playingToday'
    file_name = f'games_{TODAY_STR}.csv'
    file_to_delete = target_directory / f"games_{yesterday_str}.csv"
    full_path = os.path.join(target_directory, file_name)
    
    response = requests.get(url, timeout=15).json()
    game_week = response.get("gameWeek", [])
    today_games = []
    if game_week:
        today_games = game_week[0].get("games", [])

    # Build long rows directly: one row per team per game
    rows = []
    for game in today_games:
        home_team = game.get("homeTeam", {}).get("abbrev")
        away_team = game.get("awayTeam", {}).get("abbrev")

        rows.append({
            'team': home_team,
            'home_or_away': 'home',
            'opponent': away_team,
        })
        rows.append({
            'team': away_team,
            'home_or_away': 'away',
            'opponent': home_team,
        })
    
    if file_to_delete.exists():
        os.remove(file_to_delete)
        print(f"🗑️ Deleted old schedule: {file_to_delete.name}")
    else:
        print(f"✅ No schedule found to delete for {yesterday_str}.")
    df = pd.DataFrame(rows)
    df.to_csv(full_path, index=False)
    print(f"Data saved successfully to: {full_path}")

    


# ==========================================
# 3. THE INTERACTIVE CONTROL ROOM
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unified Data Utility Platform",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Add your command line choice argument mapping directly to your functions
    parser.add_argument(
        "action",
        choices=["skater-career", "skater-season", "gamenight", "all"],
        help=(
            "skaters-career : Download and map live NHL skaters career stats\n"
            "skaters-season : Download and map live NHL skaters season stats\n"
            "gamenight : Download today's games\n"
            "defense-career  : Download defense career stats\n"
            "defense-season  : Download defense season stats\n"
            "all     : Execute all 3 jobs sequentially"
        )
    )
    args = parser.parse_args()
    
    # Route execution based on parameters passed to sys.argv
    if args.action == "skater-career":
        execute_skater_career()
    elif args.action == "skater-season":
        execute_skater_season()
    elif args.action == "gamenight":
        execute_today_schedule()
    
    elif args.action == "all":
        print("Executing comprehensive batch sequence...")
        execute_skater_career()
        execute_skater_season()
        execute_today_schedule()
