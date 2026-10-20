# 🚨 TYPE YOUR MANUAL ADJUSTMENTS HERE
# check DailyFaceoff to see whose injuried or coming out injury,star is out or demoted
# Format: "Player Name": Multiplier
# 0.85 = -15% (Injured, demoted, tough matchup, playing with a bad center)
# 1.15 = +15% (Playing with McDavid, top PP unit, opposing goalie is out)

LINEUP_OVERRIDES = {
    # Example: Auston Matthews lost his winger, downgrade him
    #"Auston Matthews": 0.85, 
    
    # Example: Connor McDavid is playing with Draisaitl, boost him
    #"Connor McDavid": 1.15,
    
    # Example: Player returning from injury, limited minutes
    #"Jack Eichel": 0.90,

    "Sidney Crosby": 0.85,      # Rust is out/injured, Crosby's line is weaker
    "Evgeni Malkin": 0.85,      # Second line is a mismatch, volume will drop
    "Bryan Rust": 0.70,         # Lower body injury, likely out or limited
    "Egor Chinakhov": 0.75,     # Game-time decision, lower body issue
    "Rickard Rakell": 0.95,     # Will get top-line minutes, but tough matchup

    "Rasmus Dahlin": 1.05, # Dahlin is back from injury and returning to top-pair/PP1 minutes

}