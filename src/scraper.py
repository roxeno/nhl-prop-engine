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

# ==========================================
# 2. THE THREE TASK ENGINES
# ==========================================


def execute_zip_extractor():
    """Engine 1: Downloads a compressed zip for skaters and extracts it locally."""
    print(f"[{TODAY_STR}] Running Zip Extraction Utility...")
    # Example placeholder behavior using 'zipfile' and 'os'
    url = 'https://peter-tanner.com/moneypuck/downloads/seasonPlayersSummary/skaters/2026.zip'
    target_folder = DOWNLOAD_DIR/'raw/skaters'
    filename = '2026.zip'
    zip_filepath = target_folder/filename
    
    desired_extracted_name = "Season_hockeyskater.csv"

    print("Downloading ZIP file...")
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(zip_filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    print("Download complete. Extracting file...")

    # Extract the ZIP file
    # Note: This assumes the ZIP contains exactly one file you want to rename.
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        # Get the internal name of the file inside the ZIP archive
        internal_file_name = zip_ref.namelist()[0] 
    
        # Extract it to our target folder
        zip_ref.extract(internal_file_name, path=target_folder)
        extracted_file_path = target_folder / internal_file_name

    # Handle the safe renaming with iteration (+1) logic
    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"

    final_destination = target_folder / desired_extracted_name
    counter = 1

    # Loop to increment the filename if it already exists
    while final_destination.exists():
        final_destination = target_folder / f"{base_name}-{counter}{extension}"
        counter += 1

    # Perform the actual rename
    extracted_file_path.rename(final_destination)
    print(f"Success! File extracted and saved as: {final_destination.name}")

    # Clean up (Optional: deletes the temporary downloaded ZIP file)
    zip_filepath.unlink()
    print("Temporary ZIP file cleaned up.")

def execute_skater_career():
    """Engine 2: Downloads data and processes it using standard built-in csv."""
    print(f"[{TODAY_STR}] Running Raw CSV Streams...")
    # Example placeholder behavior using the native 'csv' module
    
    #Target NHL Stats API URL
    start = 0
    limit= 100

    
    target_folder = DOWNLOAD_DIR/'raw/skaters'
    desired_extracted_name = "Career_hockeyskater.csv"

    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"
    
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
    
    final_destination = target_folder / desired_extracted_name
    counter = 1
    while final_destination.exists():
                final_destination = target_folder / f"{base_name}_{counter}{extension}"
                counter += 1   
            #Save to CSV
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
            'playerTeam': home_team,
            'home_or_away': 'home',
            'opponent': away_team,
        })
        rows.append({
            'playerTeam': away_team,
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

def execute_defensive_career():
    """Engine 4: Downloads data and processes it using standard built-in csv."""
    print(f"[{TODAY_STR}] Running Raw CSV Streams...")
    # Example placeholder behavior using the native 'csv' module
    
    #--bigger sample https://api.nhle.com/stats/rest/en/team/realtime?isAggregate=true&isGame=false&sort=%5B%7B%22property%22:%22hits%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22franchiseId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20252026
    #--season https://api.nhle.com/stats/rest/en/team/realtime?isAggregate=false&isGame=false&sort=%5B%7B%22property%22:%22hits%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22teamId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20262027


    # 1. Target NHL Stats API URL
    NHL_API_URL = "https://api.nhle.com/stats/rest/en/team/realtime?isAggregate=true&isGame=false&sort=%5B%7B%22property%22:%22hits%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22franchiseId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20252026"
    target_folder = DOWNLOAD_DIR/'raw/defenders'
    desired_extracted_name = "Career_hockeyTeam_defensive.csv"
    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"


    print("Fetching live data from NHL API...")
    response = requests.get(NHL_API_URL)
    response.raise_for_status()
    
    #Extract the nested list of player records
    json_payload = response.json()
    player_data = json_payload.get("data", [])  # Targets the 'data' key array
    
    if player_data:
        #Convert directly to a structured DataFrame
        dfA = pd.DataFrame(player_data)
        dfB = pd.read_csv('../assets/allTeamNames.csv')
        
        
        #Only needed section
        dfA = dfA[['franchiseName','blockedShotsPer60']]
        df = pd.merge(dfA, dfB, on='franchiseName', how='inner')
        df = df[['blockedShotsPer60','playerTeam']]
        df = df.rename(columns={'blockedShotsPer60':'careerblockedShotsPer60'})

        final_destination = target_folder / desired_extracted_name
        counter = 1
        while final_destination.exists():
            final_destination = target_folder / f"{base_name}_{counter}{extension}"
            counter += 1   
        #Save to CSV
        df.to_csv(final_destination, index=False, encoding="utf-8")
        print(f"Success! Saved {len(df)} teams records into '{final_destination}'.")
    else:
        print("No player records found under the 'data' key.")





def execute_defensive_season():
    """Engine 5: Downloads data and processes it using standard built-in csv."""
    print(f"[{TODAY_STR}] Running Raw CSV Streams...")
    # Example placeholder behavior using the native 'csv' module
    
    #Target NHL Stats API URL
    NHL_API_URL = "https://api.nhle.com/stats/rest/en/team/realtime?isAggregate=false&isGame=false&sort=%5B%7B%22property%22:%22hits%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22teamId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20262027"
    target_folder = DOWNLOAD_DIR/'raw/defenders'
    desired_extracted_name = "Season_hockeyTeam_defensive.csv"
    base_name = Path(desired_extracted_name).stem       # e.g., "final_report"
    extension = Path(desired_extracted_name).suffix   # e.g., ".csv"
    
    
    print("Fetching live data from NHL API...")
    response = requests.get(NHL_API_URL)
    response.raise_for_status()
        
    #Extract the nested list of player records
    json_payload = response.json()
    player_data = json_payload.get("data", [])  # Targets the 'data' key array
        
    if player_data:
        #Convert directly to a structured DataFrame
        dfA = pd.DataFrame(player_data)
        dfB = pd.read_csv('../assets/allTeamNamesv2.csv')
            
            
        #Only needed section
        dfA = dfA[['teamFullName','blockedShotsPer60']]
        df = pd.merge(dfA, dfB, on='teamFullName', how='inner')
        #df = df[['blockedShotsPer60','playerTeam']]

        league_avg = df["blockedShotsPer60"].mean()
        df["leagueAvgBlockedShotsPer60"] = league_avg
        df = df[['playerTeam','blockedShotsPer60','leagueAvgBlockedShotsPer60']]
    
        final_destination = target_folder / desired_extracted_name
        #Save to CSV
        df.to_csv(final_destination, index=False, encoding="utf-8")
        print(f"Success! Saved {len(df)} teams records into '{final_destination}'.")
    else:
        print("No player records found under the 'data' key.")
    


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
        choices=["skater-career", "skater-season", "gamenight", "defense-career",'defense-season', "all"],
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
        execute_zip_extractor()
    elif args.action == "gamenight":
        execute_today_schedule()
    elif args.action == "defense-career":
        execute_defensive_career()
    elif args.action == 'defense-season' :
        execute_defensive_season()
    
    elif args.action == "all":
        print("Executing comprehensive batch sequence...")
        execute_skater_career()
        execute_zip_extractor()
        execute_today_schedule()
        execute_defensive_career()
        execute_defensive_season()
        
