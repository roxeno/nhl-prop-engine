from pathlib import Path
from scipy.stats import poisson
import pandas as pd
import numpy as np

import argparse

import csv
import sys
import os

file = Path("../data/playingToday/tonightGame.csv")
outputDir = Path("../data/built/")

weight = 0.2 #starting of season
# weight = 0.4 #middle of season
# weight = 0.8 #late of season

#def opponent_factor(opp_rate, league_rate):
    #factor = opp_rate / league_rate

#def expected_lambda(rate_per_60, toi_min, opp_factor, home):
   # if (home == "home"):
   #     home_mult = 1.05
   #else:
   #     home_mult = 0.97

#lam = rate_per_60 * (toi_min / 60) * opp_factor * home_mult

#Poisson call
#full_distribution(λ, max_n)

#playerId,name,playerTeam,home_or_away,shots_per_60,fenwick_per_60,career_shots_per_60,opponent,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
#shots_per_60,fenwick_per_60,career_shots_per_60,blockedShotsPer60,careerblockedShotsPer60,blendedavgtoimin
def execute_calculation():
    df = pd.read_csv(file)
    #blended = weight * current + (1-weight) * career
    df['playerweighted_shotsper60'] = (weight * df['shots_per_60']) + ((1-weight) * df['career_shots_per_60'])
    df['opponentweighted_blockedshotsper60'] = (weight * df['blockedShotsPer60']) + ((1-weight)* df['careerblockedShotsPer60'])
    df['opponent_factor'] = (df['leagueAvgBlockedShotsPer60']/df['opponentweighted_blockedshotsper60'])
    df['home_factor'] = np.where(df['home_or_away'] == 'home', 1.05, 0.97)
    df = df[['name','playerTeam','playerweighted_shotsper60','opponent','opponent_factor','blendedavgtoimin','home_factor']]
    df['expectedLambda'] = (df['playerweighted_shotsper60']*(df['blendedavgtoimin']/60)*df['opponent_factor']*df['home_factor'])
    for n in range(1, 6):
    # Explicitly using k and mu forces SciPy to map the variables correctly
        df[f'p_at_least_{n}'] = df['expectedLambda'].apply(lambda lam: poisson.sf(k=n-1, mu=lam))

    desired_extracted_name = "readytouse.csv"
    final_destination = outputDir / desired_extracted_name

    df.to_csv(final_destination,index=False)


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

