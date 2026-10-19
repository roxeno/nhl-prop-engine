import pandas as pd

df = pd.read_csv("../data/built/readytouse.csv")

# Just type the name, the milestone line (e.g., 4+ shots = line 4), and the decimal odds.
manual_bets = [
    {"name": "Auston Matthews", "line": 4, "odds": 1.86},
    {"name": "Macklin Celebrini", "line": 4, "odds": 1.90},
    {"name": "Nathan MacKinnon", "line": 4, "odds": 1.71},
    {"name": "Pavel Dorofeyev", "line": 3, "odds": 1.58},
    {"name": "Cutter Gauthier", "line": 3, "odds": 1.38},
]

def get_milestone_edge(player_name, line, odds):
    player_row = df[df['name'] == player_name]
    
    if player_row.empty:
        return f"{player_name} not found in CSV."
        
    player_row = player_row.iloc[0]
    
    # For milestone bets, if the line is 4+, we just look at p_at_least_4
    model_prob_col = f"p_at_least_{line}"
    
    if model_prob_col not in player_row:
        return f"Model does not have data for {line}+ shots."
        
    your_prob = player_row[model_prob_col]
    
    # Calculate Bet365 Implied Probability directly
    vegas_prob = 1 / odds
    
    # Calculate Edge
    edge = your_prob - vegas_prob
    
    status = "🔥 BET" if edge > 0.05 else ("❌ FADE" if edge < -0.05 else "➖ PASS")
    
    print(f"{player_name:<18} | {line}+ Shots | Model: {your_prob:.1%} | Vegas: {vegas_prob:.1%} | Edge: {edge:+.1%} | {status}")

    print(f"{'Player':<18} | {'Prop':<10} | {'Model':<9} | {'Vegas':<9} | {'Edge':<7} | {'Action'}")
    print("-" * 75)

for bet in manual_bets:
    get_milestone_edge(bet['name'], bet['line'], bet['odds'])