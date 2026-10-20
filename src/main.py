import argparse
import sys
from datetime import datetime

# Import your automated pipeline functions
# (Make sure these match the actual names in your other files)
from scraper import *
from trimmer import *
from analyzer import execute_calculation
from visualizer import *
# from visualizer import show_top_n, show_player_distribution

def run_gametime():
    """Runs the full automated pipeline for today."""
    print(f"\n🏒 Starting GameTime Pipeline...")
    
    # 1. Scrape
    print("Step 1: Fetching schedule & team stats...")
    execute_skater_career()
    execute_skater_season()
    execute_today_goalie()
    execute_today_schedule()
    
    # 2. Trim (Assuming these automatically find the newest raw files)
    print("Step 2: Trimming skaters & defenders...")
    execute_trimcareer()
    execute_trimskaters()
    execute_opponent()
    execute_commenceGameNight()
    
    # 3. Analyze
    print("Step 3: Calculating probabilities...")
    execute_calculation()

    print("\n✅ GameTime Complete! readytouse.csv is ready.")

def run_dashboard():
    print("Building dashboard...")
    df = pd.read_csv("../data/built/readytouse.csv")
    
    fig1 = get_top_n_fig(df)
    fig2 = get_pp_impact_fig(df)
    fig3 = get_hd_impact_fig(df)
    
    output_path = "../data/built/dashboard.html"
    with open(output_path, "w") as f:
        f.write("<html><head><title>NHL Prop Engine</title></head><body style='background-color: #f4f4f9; font-family: Arial;'>")
        f.write("<h1 style='text-align:center;'>NHL Prop Engine Dashboard</h1>")
        f.write("<h2>Top 25 Expected Shots</h2>")
        f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write("<h2>5v5 vs PP Impact</h2>")
        f.write(fig2.to_html(full_html=False, include_plotlyjs=False))
        f.write("<h2>High-Danger vs Total Volume</h2>")
        f.write(fig3.to_html(full_html=False, include_plotlyjs=False))
        f.write("</body></html>")
    print(f"✅ Dashboard saved to {output_path}!")


def main():
    # 1. Setup the parser
    parser = argparse.ArgumentParser(
    prog="python -m src.main",
    description="NHL Player Prop Quant Engine" 
    )
    
    # 2. Add ONLY the action argument
    parser.add_argument(
        "action",
        choices=["gametime", "visualize"],
        help="The pipeline stage to run."
    )
    
    # 3. Parse arguments
    args = parser.parse_args()

    # 4. Route execution
    if args.action == "gametime":
        run_gametime()
    elif args.action == "visualize":
        run_dashboard()

if __name__ == "__main__":
    main()