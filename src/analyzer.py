from scipy.stats import poisson
from lineup_override import LINEUP_OVERRIDES
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import shutil

import argparse

import csv
import sys
import os

file = Path("../data/playingToday/tonightGame.csv")
outputDir = Path("../data/built/")

today = datetime.now().strftime("%Y-%m-%d")
outputDirCache = Path("../data/logs/")
cachefile = outputDirCache / f"{today}-game.csv"

weight = 0.2 #starting of season
# weight = 0.4 #middle of season
# weight = 0.8 #late of season


#playerId,name,playerTeam,home_or_away,shots_per_60,fenwick_per_60,career_shots_per_60,opponent,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
#shots_per_60,fenwick_per_60,career_shots_per_60,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
import pandas as pd
import numpy as np
from scipy.stats import poisson
import shutil
import os

def execute_calculation():
    df = pd.read_csv(file)
    
    # 1. Apply Manual Overrides (Lineup news)
    df['manual_override'] = df['name'].map(LINEUP_OVERRIDES).fillna(1.0)
    
    # 2. Fill NaNs
    df['5on4_avg_toi_min'] = df['5on4_avg_toi_min'].fillna(0)
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].fillna(0)
    
    # 3. Blend the Rates
    df['playerweighted_shotsper60'] = (weight * df['shots_per_60']) + ((1-weight) * df['career_shots_per_60'])
    df['opponent_weighted_XGA'] = (weight * df['team_xGA_per_60']) + ((1-weight)* df['Career_team_xGA_per_60'])
    df['opponent_factor'] = (df['opponent_weighted_XGA'] / df['leagueAvgXGAper60'])
    df['home_factor'] = np.where(df['home_or_away'] == 'home', 1.05, 0.97)
    
    # 4. Context Factors (Goalie & Fatigue)
    league_avg_sv = 0.900
    df['goalie_factor'] = 1 - ((df['sv_pct'] - league_avg_sv) * 2)
    df['goalie_factor'] = df['goalie_factor'].clip(lower=0.90, upper=1.10)

    df['fatigue_multiplier'] = 1.0
    df.loc[df['player_team_b2b'] == 1, 'fatigue_multiplier'] *= 0.95
    df.loc[df['opponent_b2b'] == 1, 'fatigue_multiplier'] *= 1.05

    # ==========================================
    # TOTAL SHOTS LOGIC (5v5 vs PP)
    # ==========================================
    df['5on4_toi'] = df['5on4_avg_toi_min']
    df['5on5_toi'] = (df['blendedavgtoimin'] - df['5on4_toi']).clip(lower=0)
    
    df['total_shots'] = df['playerweighted_shotsper60'] * (df['blendedavgtoimin'] / 60)
    df['pp_shots'] = df['5on4_shots_per_60'] * (df['5on4_toi'] / 60)
    df['5v5_shots'] = (df['total_shots'] - df['pp_shots']).clip(lower=0)
    df['5v5_rate'] = np.where(df['5on5_toi'] > 0, df['5v5_shots'] / (df['5on5_toi'] / 60), df['playerweighted_shotsper60'])

    df['opp_factor_5v5'] = df['opponent_factor']
    df['opp_factor_pp'] = 1 + ((df['opp_factor_5v5'] - 1) * 0.5) 
    
    lambda_5v5 = (df['5v5_rate'] * (df['5on5_toi'] / 60)) * df['opp_factor_5v5']
    lambda_pp = (df['5on4_shots_per_60'] * (df['5on4_toi'] / 60)) * df['opp_factor_pp']
    
    df['lambda_5v5'] = lambda_5v5 * df['home_factor'] * df['goalie_factor']
    df['lambda_pp'] = lambda_pp * df['home_factor'] * df['goalie_factor']
    df['expectedLambda'] = (df['lambda_5v5'] + df['lambda_pp']) * df['fatigue_multiplier'] * df['manual_override']

    for n in range(1, 6):
        df[f'p_at_least_{n}'] = df['expectedLambda'].apply(lambda lam: poisson.sf(k=n-1, mu=lam))

    # ==========================================
    # HIGH DANGER (HD) LOGIC
    # ==========================================
    # Calculate base HD Lambda
    df['expectedLambda_hd'] = df['hd_shots_per_60'] * (df['blendedavgtoimin'] / 60)
    
    # Apply ALL the exact same context factors as total shots
    df['expectedLambda_hd'] = (
        df['expectedLambda_hd'] * 
        df['opponent_factor'] * 
        df['goalie_factor'] * 
        df['home_factor'] * 
        df['fatigue_multiplier'] * 
        df['manual_override']
    )

    for n in range(1, 4):
        df[f'p_hd_at_least_{n}'] = df['expectedLambda_hd'].apply(lambda lam: poisson.sf(k=n-1, mu=lam))

    # ==========================================
    # GOALS LOGIC (xG & Probability)
    # ==========================================
    HD_CONVERSION_RATE = 0.15
    df['expectedGoals'] = df['expectedLambda_hd'] * HD_CONVERSION_RATE
    df['p_at_least_1_goal'] = df['expectedGoals'].apply(lambda lam: poisson.sf(k=0, mu=lam))

    # ==========================================
    # SAVE
    # ==========================================
    desired_extracted_name = "readytouse.csv"
    final_destination = outputDir / desired_extracted_name
    
    final_cols = ['playerId', 'name', 'team', 'opponent', 
                  'expectedLambda', 'lambda_5v5', 'lambda_pp', 
                  'expectedLambda_hd',
                  'p_at_least_1', 'p_at_least_2', 'p_at_least_3', 'p_at_least_4', 'p_at_least_5',
                  'p_hd_at_least_1', 'p_hd_at_least_2', 'p_hd_at_least_3',
                  'playerweighted_shotsper60', 'hd_shots_per_60', 'blendedavgtoimin', 'sv_pct', 
                  'player_team_b2b', 'opponent_b2b', 'fatigue_multiplier', 'manual_override', 
                  'expectedGoals', 'p_at_least_1_goal']
    
    df[final_cols].to_csv(final_destination, index=False)
    shutil.copy(final_destination, cachefile)
    print("Calculation complete with 5v5/PP splits, HD Shots, and Expected Goals!")
    
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
        choices=["analyze"],
        help=(
            "analyze   : analyze the game"
        )
    )

    args = parser.parse_args()

    if args.action == "analyze":
        execute_calculation()
   


if __name__ == "__main__":
    main()

