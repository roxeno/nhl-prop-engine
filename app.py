import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.visualizer import (
    get_top_n_fig, get_pp_impact_fig, 
    get_hd_impact_fig, get_goal_scorers_fig
)

# Layout="wide" allows the columns to spread out on Desktop
st.set_page_config(page_title="NHL Prop Engine", page_icon="🏒", layout="wide")

# Custom CSS to fix mobile spacing
st.markdown("""
    <style>
    /* Make the container padding smaller on mobile */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 1rem; padding-right: 1rem; }
    /* Hero Banner Styling */
    .hero-banner {
        background-color: #1e1e1e; padding: 15px; border-radius: 10px;
        text-align: center; border: 1px solid #333; margin-bottom: 10px;
    }
    .hero-text { color: #e0e0e0; font-size: 1rem; margin: 0; }
    .hero-name { color: #ff4b4b; font-size: 2rem; font-weight: bold; margin: 5px 0; }
    </style>
""", unsafe_allow_html=True)

st.title("🏒 NHL Prop Engine")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error(f"Data not found at {CSV_PATH}. Run the pipeline first.")
    st.stop()

# HERO BANNER
most_dangerous = df.sort_values("p_at_least_1_goal", ascending=False).iloc[0]
st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-text">🚨 Most Likely to Score Tonight 🚨</p>
        <p class="hero-name">{most_dangerous['name']}</p>
        <p class="hero-text">
            vs {most_dangerous['opponent']} ({most_dangerous['sv_pct']:.3f} SV%) <br>
            xG: <b>{most_dangerous['expectedGoals']:.2f}</b> | 
            P(Score): <b>{most_dangerous['p_at_least_1_goal']:.1%}</b>
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# TOP ROW (Two columns on desktop, stacked on mobile)
col1, col2, col3 = st.columns(3)
top_player = df.sort_values("expectedLambda", ascending=False).iloc[0]
with col1:
    st.metric(label="Top Volume (λ)", value=f"{top_player['expectedLambda']:.2f}", help=f"{top_player['name']}")
with col2:
    st.metric(label="Top HD Volume (λ)", value=f"{most_dangerous['expectedLambda_hd']:.2f}", help=f"{most_dangerous['name']}")
with col3:
    st.metric(label="Total Players", value=len(df), help="Players playing tonight")

st.divider()

# THE 4 TABS
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Volume", "⚖️ 5v5 vs PP", "🎯 High Danger", "🥅 Goals"])

with tab1:
    st.plotly_chart(get_top_n_fig(df, n=25), use_container_width=True)

with tab2:
    st.plotly_chart(get_pp_impact_fig(df, n=20), use_container_width=True)

with tab3:
    st.plotly_chart(get_hd_impact_fig(df, n=40), use_container_width=True)

with tab4:
    st.plotly_chart(get_goal_scorers_fig(df, n=25), use_container_width=True)

# DATA TABLE
st.divider()
with st.expander("📋 View Raw Data Table"):
    # On mobile, only show the most important columns
    display_cols = ['name', 'team', 'opponent', 'expectedLambda', 'expectedLambda_hd', 'expectedGoals', 'p_at_least_1_goal', 'sv_pct']
    st.dataframe(
        df[display_cols].sort_values("p_at_least_1_goal", ascending=False),
        use_container_width=True,
        hide_index=True
    )