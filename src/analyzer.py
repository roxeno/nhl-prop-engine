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

games_played = 12
OPP_WEIGHT = games_played / (games_played + 15)



#playerId,name,playerTeam,home_or_away,shots_per_60,fenwick_per_60,career_shots_per_60,opponent,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
#shots_per_60,fenwick_per_60,career_shots_per_60,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
import pandas as pd
import numpy as np
from scipy.stats import poisson
import shutil
import os

def execute_calculation():
    df = pd.read_csv(file)
    # 🚨 FIX: If a player is listed twice, keep the one with the highest blended TOI
    df = df.sort_values('blendedavgtoimin', ascending=False)
    df = df.drop_duplicates(subset=['playerId'], keep='first')
    
    # 1. Apply Manual Overrides (Lineup news)
    df['manual_override'] = df['name'].map(LINEUP_OVERRIDES).fillna(1.0)
    
    # 2. Fill NaNs (Expanded)
    df['5on4_avg_toi_min'] = df['5on4_avg_toi_min'].fillna(0)
    df['5on4_shots_per_60'] = df['5on4_shots_per_60'].fillna(0)
    
    # 🚨 ADD THESE: Fix missing data that causes infinite/NaN lambdas
    df['blendedavgtoimin'] = df['blendedavgtoimin'].fillna(0)
    df['team_xGA_per_60'] = df['team_xGA_per_60'].fillna(df['leagueAvgXGAper60'])
    df['Career_team_xGA_per_60'] = df['Career_team_xGA_per_60'].fillna(df['leagueAvgXGAper60'])
    df['sv_pct'] = df['sv_pct'].fillna(0.905) # default league average


    # 🚨 FIX #4: Replace the 0.8 placeholder with the actual league-average HD rate
    LEAGUE_HD_PER_60 = (
        df['I_F_highDangerShots'].sum() /
        (df['icetime'].sum() / 3600.0)
    ).round(2)
    # If blended_hd_per_60 is missing or NaN, fall back to league average (not 0.8)
    df['blended_hd_per_60'] = df['blended_hd_per_60'].fillna(LEAGUE_HD_PER_60)
    
    # 3. Blend the Rates
    df['opponent_weighted_XGA'] = (OPP_WEIGHT * df['team_xGA_per_60']) + \
                              ((1 - OPP_WEIGHT) * df['Career_team_xGA_per_60'])
    df['opponent_factor'] = (df['opponent_weighted_XGA'] / df['leagueAvgXGAper60'])
    df['home_factor'] = np.where(df['home_or_away'] == 'home', 1.05, 0.97)
    
    # Shrink goalie SV% toward league mean, then scale to shots effect
    LEAGUE_SV = 0.905
    SHRINK_GAMES = 20
    g_sv = df['sv_pct'].fillna(LEAGUE_SV)
    # assume we have goalie games played; if not, use a flat 0.7 weight
    g_sv_shrunk = 0.7 * g_sv + 0.3 * LEAGUE_SV
    df['goalie_factor'] = (1 - (g_sv_shrunk - LEAGUE_SV) * 3).clip(0.92, 1.08)

    df['fatigue_multiplier'] = 1.0
    df.loc[df['player_team_b2b'] == 1, 'fatigue_multiplier'] *= 0.95
    df.loc[df['opponent_b2b'] == 1, 'fatigue_multiplier'] *= 1.05

    # ==========================================
    # TOTAL SHOTS LOGIC (5v5 vs PP)
    # ==========================================
    df['5on4_toi'] = df['5on4_avg_toi_min']
    df['5on5_toi'] = (df['blendedavgtoimin'] - df['5on4_toi']).clip(lower=0)
    
    df['total_shots'] = df['blended_shots_per60'] * (df['blendedavgtoimin'] / 60)
    df['pp_shots'] = df['5on4_shots_per_60'] * (df['5on4_toi'] / 60)
    df['5v5_shots'] = (df['total_shots'] - df['pp_shots']).clip(lower=0)
    df['5v5_rate'] = np.where(df['5on5_toi'] > 0, df['5v5_shots'] / (df['5on5_toi'] / 60), df['blended_shots_per60'])

    df['opp_factor_5v5'] = df['opponent_factor']
    df['opp_factor_pp'] = 1 + ((df['opp_factor_5v5'] - 1) * 0.5) 
    
    lambda_5v5 = (df['5v5_rate'] * (df['5on5_toi'] / 60)) * df['opp_factor_5v5']
    lambda_pp = (df['5on4_shots_per_60'] * (df['5on4_toi'] / 60)) * df['opp_factor_pp']
    
    df['lambda_5v5'] = lambda_5v5 * df['home_factor'] * df['goalie_factor']
    df['lambda_pp'] = lambda_pp * df['home_factor'] * df['goalie_factor']
    df['expectedLambda'] = (df['lambda_5v5'] + df['lambda_pp']) * df['fatigue_multiplier'] * df['manual_override']

    for n in range(1, 6):
        df[f'p_at_least_{n}'] = df['expectedLambda'].apply(
        lambda lam: 0.0 if lam <= 0 else poisson.sf(k=n-1, mu=lam)
        )

    # HD fraction from blended rates (stable, player-specific signal)
    df['hd_fraction'] = (df['blended_hd_per_60'] / df['blended_shots_per60'].replace(0, np.nan)).clip(0.10, 0.55)
    df['hd_fraction'] = df['hd_fraction'].fillna(0.25)   # fallback to league-typical

    # HD lambda = total lambda × HD fraction (correct TOI split + context already baked in)
    df['expectedLambda_hd'] = df['expectedLambda'] * df['hd_fraction']

    # 🚨 FIX #3: Zero out HD lambda when total expectedLambda is 0 (player won't play)
    df.loc[df['expectedLambda'] <= 0, 'expectedLambda_hd'] = 0.0

    for n in range(1, 4):
        df[f'p_hd_at_least_{n}'] = df['expectedLambda_hd'].apply(lambda lam: poisson.sf(k=n-1, mu=lam))

    # ==========================================
    # GOALS LOGIC (xG & Probability)
    # ==========================================
    df['expectedLambda'] = df['expectedLambda'].replace([np.inf, -np.inf], np.nan).fillna(0)
    df['expectedLambda_hd'] = df['expectedLambda_hd'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Fallbacks if trimmer didn't export the blend columns (defensive)
    df['blended_hd_pct'] = df['blended_hd_pct'].fillna(0.15)
    df['blended_non_hd_pct'] = df['blended_non_hd_pct'].fillna(0.05)

    # True HD / non-HD split
    df['expectedGoals'] = (
        df['expectedLambda_hd'] * df['blended_hd_pct']
        + (df['expectedLambda'] - df['expectedLambda_hd']) * df['blended_non_hd_pct']
    )

        # Binomial probability of ≥1 goal
    # effective_sh_pct = expectedGoals / expectedLambda
    # (guaranteed to equal the blend: HD_frac × hd_sh_pct + non_HD_frac × non_hd_sh_pct)
    df['effective_sh_pct'] = (
        df['expectedGoals'] / df['expectedLambda'].replace(0, np.nan)
    ).fillna(0.10)

    df['p_at_least_1_goal'] = np.where(
        df['expectedLambda'] > 0,
        1 - (1 - df['effective_sh_pct']) ** df['expectedLambda'],
        0.0
    )


    # ==========================================
    # SAVE
    # ==========================================
    desired_extracted_name = "readytouse.csv"
    final_destination = outputDir / desired_extracted_name
    
    # 🚨 FIX #2: manual_override is now applied to expectedLambda (line above), so it's accurate.
    # Also swap hd_shots_per_60 → blended_hd_per_60 in final_cols so the output reflects what was used.
    final_cols = ['playerId', 'name', 'team', 'opponent', 
                  'expectedLambda', 'lambda_5v5', 'lambda_pp', 
                  'expectedLambda_hd',
                  'p_at_least_1', 'p_at_least_2', 'p_at_least_3', 'p_at_least_4', 'p_at_least_5',
                  'p_hd_at_least_1', 'p_hd_at_least_2', 'p_hd_at_least_3',
                  'blended_shots_per60', 'blended_hd_per_60', 'blendedavgtoimin', 'blended_hd_pct','blended_non_hd_pct','sv_pct', 
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

