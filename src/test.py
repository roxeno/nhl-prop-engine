import pandas as pd

df = pd.read_csv("../data/built/readytouse.csv")   # or whatever file pea.py reads
"""
print("expectedLambda distribution:")
print(df['expectedLambda'].describe())

print("\nPlayers with expectedLambda > 0:", (df['expectedLambda'] > 0).sum())
print("Players with expectedLambda == 0:", (df['expectedLambda'] == 0).sum())
print("Players with expectedLambda NaN:", df['expectedLambda'].isna().sum())

print("\nTop 10 by expectedLambda:")
print(df.nlargest(10, 'expectedLambda')[['name', 'expectedLambda', 'p_at_least_1', 'p_at_least_3']])

# 1. The rate: is 5v5_rate reasonable?
print("5v5_rate (shots per 60):")
print(df['5v5_rate'].describe())
# Expected: mean ~4.0-5.0, max ~10-12

# 2. The TOI: is 5on5_toi reasonable?
print("\n5on5_toi (minutes):")
print(df['blendedavgtoimin'].describe())
# Expected: mean ~12-13, max ~18-20

# 3. The multipliers: do they sum to ~1.0 on average?
print("\nopp_factor_5v5:", df['opp_factor_5v5'].describe() if 'opp_factor_5v5' in df.columns else "not in log")
print("home_factor:", df['home_factor'].describe() if 'home_factor' in df.columns else "not in log")
print("goalie_factor:", df['goalie_factor'].describe() if 'goalie_factor' in df.columns else "not in log")

# 4. The PP split: is lambda_pp contributing?
print("\nlambda_5v5:", df['lambda_5v5'].describe() if 'lambda_5v5' in df.columns else "not in log")
print("lambda_pp:", df['lambda_pp'].describe() if 'lambda_pp' in df.columns else "not in log")
print("Sum lambda_5v5:", df['lambda_5v5'].sum() if 'lambda_5v5' in df.columns else "?")
print("Sum lambda_pp:", df['lambda_pp'].sum() if 'lambda_pp' in df.columns else "?")

# 5. The big one: blended_shots_per60
print("\nblended_shots_per60:")
print(df['blended_shots_per60'].describe() if 'blended_shots_per60' in df.columns else "not in log")
# Expected: mean ~5.0, max ~12"""

