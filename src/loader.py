import pandas as pd
from pathlib import Path
import os

# Define your paths
RAW_DIR = Path("../data/raw/")
OUTPUT_FILE = Path("../data/career/career_hd_priors.csv")

def build_career_data():
    # 1. Find all raw files (adjust the pattern to match your filenames)
    # Assuming you downloaded: skaters_2023.csv, skaters_2024.csv, skaters_2025.csv
    files = list(RAW_DIR.glob("skaters_*.csv"))
    
    if not files:
        print("❌ No raw files found in data/raw/ matching 'skaters_*.csv'")
        return

    print(f"Found {len(files)} files. Stacking...")
    
    all_dfs = []
    for f in files:
        print(f"  -> Loading {f.name}")
        df = pd.read_csv(f)
        
        # Filter to only 'all' situations (to avoid double counting)
        df = df[df['situation'] == 'all']
        
        # Keep ONLY the columns we need for career priors to save memory
        cols_to_keep = ['playerId', 'name', 'games_played','I_F_highDangerShots', 'I_F_shotsOnGoal', 'icetime']
        
        # Safety check: if your older files don't have HD shots, default to 0
        if 'I_F_highDangerShots' not in df.columns:
            df['I_F_highDangerShots'] = 0
            
        all_dfs.append(df[cols_to_keep])

    # 2. Combine them all into one massive dataframe
    master_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Total combined rows: {len(master_df)}")

    # 3. Group by player and SUM their entire career
    print("Calculating career totals...")
    career_df = master_df.groupby(['playerId', 'name']).agg(
        career_games=('games_played', 'sum'),
        career_hd_shots=('I_F_highDangerShots', 'sum'),
        career_total_shots=('I_F_shotsOnGoal', 'sum'),
        career_icetime=('icetime', 'sum'),
    ).reset_index()
    # 4. Calculate the career priors (per 60)
    # Avoid division by zero by adding a tiny safety net
    career_df['career_hd_per_60'] = career_df['career_hd_shots'] / (career_df['career_icetime'] / 3600 + 0.001)
    career_df['career_shots_per_60'] = career_df['career_total_shots'] / (career_df['career_icetime'] / 3600 + 0.001)

    # 5. Save to the career folder
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    career_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Success! Saved {len(career_df)} player career priors to {OUTPUT_FILE}")

if __name__ == "__main__":
    build_career_data()