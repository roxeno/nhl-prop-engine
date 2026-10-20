🏒 NHL Prop Engine
A fully automated, quantitative data pipeline for projecting NHL Player Shots on Goal.

This project pulls raw data from the NHL API and MoneyPuck, applies advanced statistical modeling, and uses a Poisson distribution to calculate the exact probability of a player hitting specific shot milestones.

🚀 Features
Bayesian Shrinkage: Blends current season performance with career baselines to remove small-sample noise.

5v5 vs. Power Play Splits: Calculates separate expected lambdas for even-strength and power-play situations.

Opponent xGA Adjustment: Adjusts player volume based on the opponent's Expected Goals Against (xGA).

Goalie SV% Context: Suppresses or boosts projections based on the specific starting goalie's Save Percentage.

High-Danger (HD) Ratios: Evaluates shot quality by tracking the percentage of shots that come from high-danger areas.

Fatigue Multiplier: Automatically detects Back-to-Back (B2B) games via local schedule caching.

Interactive Dashboard: A fast, single-page HTML dashboard built with Plotly and Streamlit.

🛠️ Tech Stack
Python: Core logic and data manipulation.

Pandas & NumPy: Data cleaning, merging, and mathematical modeling.

SciPy: Poisson distribution probability calculations.

Plotly & Streamlit: Interactive data visualization.

NHL API & MoneyPuck: Open-source hockey data.

🧠 The Math
The engine calculates Expected Lambda (
λ
λ) using the following logic:

Base Rate: Blended Shots per 60 (Current Season + Career).

TOI Split: Separates total ice time into 5v5 and 5v4 (Power Play).

Context Multipliers: Applies Opponent xGA, Goalie SV%, Home/Away, and B2B Fatigue.

Poisson Distribution: Converts 
λ
λ into a probability distribution for 
k
k shots.

🤝 Acknowledgments
This project was built through a unique human-AI collaboration. The architecture, pipeline logic, and sports analytics domain knowledge were directed by the human creator. However, the AI (acting as a pair-programmer, debugger, and statistical consultant) was heavily involved in writing the code, untangling pandas merge conflicts, fixing TOI decimal errors, and structuring the mathematical models.

🏃‍♂️ How to Run
Install dependencies: pip install -r requirements.txt

Run the daily pipeline: python -m src.main gametime

Build the visual dashboard: python -m src.main visualize

Open the Streamlit app: streamlit run app.py

This response is AI-generated, for reference only.
