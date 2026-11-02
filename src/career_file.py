import pandas as pd
import numpy as np

file_names = ['../data/raw/skaters_2026.csv','../data/raw/skaters_2025.csv','../data/raw/skaters_2024.csv']

def merge_careerfile():
    print("merging the files")
    df_list = [pd.read_csv(file) for file in file_names]
    master_df = pd.concat(df_list, ignore_index=True)

    player_career_summary = master_df.groupby(['playerId', 'name']).agg(
    seasons_played=('season', 'count'),       # Counts how many seasons they appear in (1, 2, or 3)
    career_games=('games_played', 'sum'),     # Total games across all available years
    total_goals=('I_F_goals', 'sum'),
    total_hd_goals = ('I_F_highDangerGoals','sum'),
    total_hd_shots = ('I_F_highDangerShots', 'sum'),
    total_sog =('I_F_shotsOnGoal', 'sum'),
    total_missed_shots = ('I_F_missedShots','sum'),
    career_icetime=('icetime', 'sum')          # Average TOI across active seasons
    ).reset_index()
    #fix this looking at trimmer codes pls
    CAREER_HD_SH_PCT = sum(player_career_summary['total_hd_goals'])/sum(player_career_summary['total_hd_shots'])

    player_career_summary['career_shots_per_60'] = player_career_summary['total_sog'] / (player_career_summary['career_icetime']/3600)
    player_career_summary['career_hd_per_60'] = player_career_summary['total_hd_shots'] / (player_career_summary['career_icetime']/3600)
    player_career_summary['career_fenwick_per_60'] = ( player_career_summary['total_sog']  + player_career_summary['total_missed_shots'])/ (player_career_summary['career_icetime']/3600)
    player_career_summary['career_non_hd_goals'] = player_career_summary['total_goals'] - player_career_summary['total_hd_goals']
    player_career_summary['career_non_hd_shots'] = player_career_summary['total_sog'] - player_career_summary['total_hd_shots']
    player_career_summary['career_hd_sh_pct'] = (player_career_summary['total_hd_goals'] / player_career_summary['total_hd_shots'].replace(0, np.nan)).fillna(CAREER_HD_SH_PCT).clip(0.00, 0.50)
    CAREER_NON_SH_PCT = sum(player_career_summary['career_non_hd_goals'])/ sum(player_career_summary['career_non_hd_shots'])
    player_career_summary['career_non_hd_sh_pct'] = (player_career_summary['career_non_hd_goals'] / player_career_summary['career_non_hd_shots'].replace(0, np.nan)).fillna(CAREER_NON_SH_PCT).clip(0.00, 0.30)
    # Step 4: Save your new combined master file
    print("done merging, setting path directory")
    player_career_summary.to_csv('../assets/Careerprior_hockeyskater.csv', index=False)
    print("done and downloaded!")


merge_careerfile()

