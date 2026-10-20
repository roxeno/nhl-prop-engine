import streamlit as st
import pandas as pd
import sys
import os
from src.visualizer import get_top_n_fig, get_pp_impact_fig, get_hd_impact_fig,get_top_5_distributions

#streamlit run app.py

# Set page config
st.set_page_config(page_title="NHL Prop Engine", layout="wide")

st.title("🏒 NHL Prop Engine Dashboard")

# 🚨 FIX: Build the absolute path to the CSV
BASE_DIR = sys.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "built", "readytouse.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error(f"Data not found at {CSV_PATH}. Please run your gametime pipeline first.")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4= st.tabs(["Top 25 Expected Shots", "5v5 vs PP Impact", "High-Danger Shots", "Top 5 expected shots"])

with tab1:
    st.plotly_chart(get_top_n_fig(df), use_container_width=True)

with tab2:
    st.plotly_chart(get_pp_impact_fig(df), use_container_width=True)

with tab3:
    st.plotly_chart(get_hd_impact_fig(df), use_container_width=True)

with tab4:
    st.plotly_chart(get_top_5_distributions(df), use_container_width=True)

with st.expander("See Raw Data Table"):
    st.dataframe(df)