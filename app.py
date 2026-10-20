import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.visualizer import get_top_n_fig, get_pp_impact_fig, get_hd_impact_fig, get_goal_scorers_fig

st.set_page_config(page_title="NHL Prop Engine", page_icon="🏒", layout="wide")

st.title("🏒 NHL Prop Engine")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error(f"Data not found at {CSV_PATH}. Run the pipeline first.")
    st.stop()

# --- HERO BANNER (Updated to show the most dangerous Goal Scorer) ---
most_dangerous = df.sort_values("p_at_least_1_goal", ascending=False).iloc[0]

st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-text">🚨 Most Likely to Score Tonight 🚨</p>
        <p class="hero-name">{most_dangerous['name']}</p>
        <p class="hero-text">
            vs {most_dangerous['opponent']} ({most_dangerous['sv_pct']:.3f} SV%) <br>
            Expected Goals: <b>{most_dangerous['expectedGoals']:.2f}</b> | 
            P(Score): <b>{most_dangerous['p_at_least_1_goal']:.1%}</b>
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# --- NEW 4-TAB LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Top Volume", "⚖️ 5v5 vs PP", "🎯 High Danger", "🥅 Goal Scorers"])

with tab1:
    st.plotly_chart(get_top_n_fig(df, n=25), use_container_width=True)

with tab2:
    st.plotly_chart(get_pp_impact_fig(df, n=20), use_container_width=True)

with tab3:
    st.plotly_chart(get_hd_impact_fig(df, n=40), use_container_width=True)

with tab4:
    st.plotly_chart(get_goal_scorers_fig(df, n=25), use_container_width=True)

# --- DATA TABLE ---
st.divider()
with st.expander("📋 View Raw Data Table"):
    display_cols = ['name', 'team', 'opponent', 'expectedLambda', 'expectedLambda_hd', 'expectedGoals', 'p_at_least_1_goal', 'sv_pct']
    st.dataframe(
        df[display_cols].sort_values("p_at_least_1_goal", ascending=False),
        use_container_width=True,
        hide_index=True
    )