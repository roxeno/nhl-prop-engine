import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.visualizer import get_top_n_fig, get_pp_impact_fig, get_hd_impact_fig

st.set_page_config(page_title="NHL Prop Engine", page_icon="🏒", layout="wide")

# Custom CSS for the Hero Banner
st.markdown("""
    <style>
    .hero-banner {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    .hero-text {
        color: #e0e0e0;
        font-size: 1.2rem;
        margin: 0;
    }
    .hero-name {
        color: #ff4b4b; /* Streamlit red */
        font-size: 2.5rem;
        font-weight: bold;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏒 NHL Prop Engine")

# Load Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error(f"Data not found at {CSV_PATH}. Run the pipeline first.")
    st.stop()

# --- THE HERO BANNER ---
# Find the player with the highest High-Danger Lambda (Most Dangerous)
most_dangerous = df.sort_values("expectedLambda_hd", ascending=False).iloc[0]

st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-text">🚨 Most Dangerous Player Tonight 🚨</p>
        <p class="hero-name">{most_dangerous['name']}</p>
        <p class="hero-text">vs {most_dangerous['opponent']} (Goalie SV%: {most_dangerous['sv_pct']:.3f})</p>
    </div>
""", unsafe_allow_html=True)

# --- THE METRICS ROW ---
# We'll keep the three metrics, but base them on the top overall volume player
top_player = df.sort_values("expectedLambda", ascending=False).iloc[0]
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Top Volume (λ)", 
        value=f"{top_player['expectedLambda']:.2f}", 
        help=f"{top_player['name']}"
    )
with col2:
    st.metric(
        label="Top HD Volume (λ)", 
        value=f"{top_player['expectedLambda_hd']:.2f}", 
        help=f"{most_dangerous['name']}"
    )
with col3:
    st.metric(
        label="Total Players", 
        value=len(df), 
        help="Players playing tonight"
    )

st.divider()

# --- CHARTS ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("### 🔥 Top 25 Expected Shots")
    fig1 = get_top_n_fig(df, n=25)
    fig1.update_layout(height=800) 
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.markdown("### ⚖️ 5v5 vs Power Play")
    fig2 = get_pp_impact_fig(df, n=20)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🎯 High Danger vs Volume")
    fig3 = get_hd_impact_fig(df, n=40)
    fig3.update_layout(height=450)
    st.plotly_chart(fig3, use_container_width=True)

# --- RAW DATA ---
st.divider()
with st.expander("📋 View Raw Data Table"):
    display_cols = ['name', 'team', 'opponent', 'expectedLambda', 'expectedLambda_hd', 'sv_pct']
    st.dataframe(
        df[display_cols].sort_values("expectedLambda", ascending=False),
        use_container_width=True,
        hide_index=True
    )