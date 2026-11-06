import pandas as pd
import numpy as np

file_names = [
    '../data/raw/skaters_2026.csv',
    '../data/raw/skaters_2025.csv',
    '../data/raw/skaters_2024.csv'
]


def merge_careerfile():
    print("merging the files")
    df_list = [pd.read_csv(file) for file in file_names]
    master_df = pd.concat(df_list, ignore_index=True)

    # ── FIX 1: exclude the 'all' row before summing situations ──
    situations_only = master_df[master_df['situation'].isin(['5on5', '5on4', '4on5'])]

    player_career_summary = situations_only.groupby(['playerId', 'name']).agg(
        seasons_played=('season', 'nunique'),
        total_goals=('I_F_goals', 'sum'),
        total_hd_goals=('I_F_highDangerGoals', 'sum'),
        total_hd_shots=('I_F_highDangerShots', 'sum'),
        total_sog=('I_F_shotsOnGoal', 'sum'),
        total_missed_shots=('I_F_missedShots', 'sum'),
        career_icetime=('icetime', 'sum'),
    ).reset_index()

    # ── FIX 2: get career_games from the 'all' row (one per season) ──
    all_rows = master_df[master_df['situation'] == 'all']
    games_per_season = all_rows.groupby(
        ['playerId', 'name', 'season']
    )['games_played'].first().reset_index()
    career_games = games_per_season.groupby(
        ['playerId', 'name']
    )['games_played'].sum().reset_index()
    career_games.columns = ['playerId', 'name', 'career_games']

    player_career_summary = player_career_summary.merge(
        career_games, on=['playerId', 'name'], how='left'
    )

    # ── HD / non-HD splits (MUST come before league averages) ──
    player_career_summary['career_non_hd_goals'] = (
        player_career_summary['total_goals'] - player_career_summary['total_hd_goals']
    )
    player_career_summary['career_non_hd_shots'] = (
        player_career_summary['total_sog'] - player_career_summary['total_hd_shots']
    )

    # ── League averages (now the non-HD columns exist) ──
    CAREER_HD_SH_PCT = (
        player_career_summary['total_hd_goals'].sum()
        / player_career_summary['total_hd_shots'].sum()
    )
    CAREER_NON_SH_PCT = (
        player_career_summary['career_non_hd_goals'].sum()
        / player_career_summary['career_non_hd_shots'].sum()
    )

    # ── Career rates ──
    player_career_summary['career_shots_per_60'] = (
        player_career_summary['total_sog']
        / (player_career_summary['career_icetime'] / 3600)
    )
    player_career_summary['career_hd_per_60'] = (
        player_career_summary['total_hd_shots']
        / (player_career_summary['career_icetime'] / 3600)
    )
    player_career_summary['career_fenwick_per_60'] = (
        player_career_summary['total_sog'] + player_career_summary['total_missed_shots']
    ) / (player_career_summary['career_icetime'] / 3600)

    # ── HD / non-HD shooting percentages ──
    player_career_summary['career_hd_sh_pct'] = (
        player_career_summary['total_hd_goals']
        / player_career_summary['total_hd_shots'].replace(0, np.nan)
    ).fillna(CAREER_HD_SH_PCT).clip(0.00, 0.50)

    player_career_summary['career_non_hd_sh_pct'] = (
        player_career_summary['career_non_hd_goals']
        / player_career_summary['career_non_hd_shots'].replace(0, np.nan)
    ).fillna(CAREER_NON_SH_PCT).clip(0.00, 0.30)

    print("done merging, setting path directory")
    player_career_summary.to_csv('../assets/Careerprior_hockeyskater.csv', index=False)
    print("done and downloaded!")


merge_careerfile()