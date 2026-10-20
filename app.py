import sys
import os
import streamlit as st
import pandas as pd

# Ensure Python finds the src folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.visualizer import get_top_n_fig, get_pp_impact_fig, get_hd_impact_fig

# 1. Mobile Page Config
st.set_page_config(
    page_title="NHL Prop Engine", 
    page_icon="🏒", 
    layout="centered" # "centered" looks much better on mobile than "wide"
)

# 2. Custom CSS to make it pop on mobile
st.markdown("""
    <style>
    /* Make the main container act like a mobile app */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Style the headers */
    h1 { font-size: 2rem !important; text-align: center; }
    h2 { font-size: 1.5rem !important; margin-top: 1rem; }
    /* Style the metric boxes */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header
st.title("🏒 NHL Prop Engine")
st.markdown("<p style='text-align: center; color: gray;'>Automated Player Projections</p>", unsafe_allow_html=True)

# 4. Load Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error("Data not found. Run the pipeline first.")
    st.stop()

# 5. Top Metrics Row (Looks great on mobile)
st.markdown("### 📊 Tonight's Leaders")
col1, col2, col3 = st.columns(3)

# Get the top player
top_player = df.sort_values("expectedLambda", ascending=False).iloc[0]

with col1:
    st.metric(
        label="Top λ", 
        value=f"{top_player['expectedLambda']:.2f}", 
        help=f"{top_player['name']}"
    )
with col2:
    st.metric(
        label="Top HD λ", 
        value=f"{top_player['expectedLambda_hd']:.2f}", 
        help="High Danger Expected Shots"
    )
with col3:
    st.metric(
        label="Players", 
        value=len(df), 
        help="Total players playing tonight"
    )

st.divider()

# 6. Tabs for the Charts (Perfect for scrolling on mobile)
tab1, tab2, tab3 = st.tabs(["🔥 Top 25", "⚖️ 5v5 vs PP", "🎯 High Danger"])

with tab1:
    st.markdown("**Top 25 Expected Shots**")
    # Use_container_width=False ensures it scales to the phone width
    st.plotly_chart(get_top_n_fig(df, n=25), use_container_width=True)

with tab2:
    st.markdown("**5v5 vs Power Play Volume**")
    st.plotly_chart(get_pp_impact_fig(df, n=20), use_container_width=True)

with tab3:
    st.markdown("**Total Volume vs High Danger**")
    st.plotly_chart(get_hd_impact_fig(df, n=40), use_container_width=True)

# 7. Mobile-Friendly Data Table
st.divider()
with st.expander("📋 View Raw Data Table"):
    # On mobile, we only want to show the most important columns
    display_cols = ['name', 'team', 'opponent', 'expectedLambda', 'expectedLambda_hd', 'sv_pct']
    st.dataframe(
        df[display_cols].sort_values("expectedLambda", ascending=False),
        use_container_width=True,
        hide_index=True
    )