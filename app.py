import sys
import os
import streamlit as st
import pandas as pd

# Ensure Python finds the src folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.visualizer import get_top_n_fig, get_pp_impact_fig, get_hd_impact_fig

# 1. Layout Config (Wide for desktop, auto-stacks for mobile)
st.set_page_config(
    page_title="NHL Prop Engine", 
    page_icon="🏒", 
    layout="wide" 
)

# Custom CSS for clean UI
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    h1 { font-size: 2.5rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🏒 NHL Prop Engine")

# 2. Load Data (Absolute path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error(f"Data not found at {CSV_PATH}. Run the pipeline first.")
    st.stop()

# 3. Top Metrics Row
top_player = df.sort_values("expectedLambda", ascending=False).iloc[0]
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Top λ", value=f"{top_player['expectedLambda']:.2f}", help=f"{top_player['name']}")
with col2:
    st.metric(label="Top HD λ", value=f"{top_player['expectedLambda_hd']:.2f}", help="High Danger Expected Shots")
with col3:
    st.metric(label="Players", value=len(df), help="Total players playing tonight")

st.divider()

# 4. Desktop Grid Layout (Auto-stacks on mobile)
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
    fig3.update_layout(height=380)
    st.plotly_chart(fig3, use_container_width=True)

# 5. Raw Data Table
st.divider()
with st.expander("📋 View Raw Data Table"):
    display_cols = ['name', 'team', 'opponent', 'expectedLambda', 'expectedLambda_hd', 'sv_pct']
    st.dataframe(
        df[display_cols].sort_values("expectedLambda", ascending=False),
        use_container_width=True,
        hide_index=True
    )