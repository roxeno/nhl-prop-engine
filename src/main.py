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

if __name__ == "__main__":
    main()