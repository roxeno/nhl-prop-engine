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

    # penguins
    "Sidney Crosby": 0.85,      # Rust is out/injured, Crosby's line is weaker
    "Evgeni Malkin": 0,      # Second line is a mismatch, volume will drop
    "Bryan Rust": 0.70,         # Lower body injury, likely out or limited
    "Rickard Rakell": 0.95,     # Will get top-line minutes, but tough matchup


    "Quinton Byfield": 0, 
    "Nick Suzuki" :0,
    "Cole Caufield":0.80,
    "Juraj Slafovsky":0.80,
    "Aleksander Barkov": 0,
    "Brad Marchand": 0, # (Florida Panthers): Out 6 weeks with a lower-body injury.
    "Igor Shesterkin": 0, # (New York Rangers): Out for the season following knee surgery.
    "Taylor Hall":0, #(Chicago Blackhawks): On injured reserve, targeting a return around November 7.

    # Toronto Maple Leafs
    "John Tavares": 0,           # Placed on IR; out for multi-game road trip
    "Mitch Marner": 0.80,         # DTD (Personal); high risk if late scratch
    "William Nylander": 1.15,     # Massive volume spike with Tavares/Marner out
    "Elvis Merzlikins":0, #(Toronto Maple Leafs): Out 4 to 6 months with a shoulder injury.
    "Chris Tanev":0, #(Toronto Maple Leafs): On injured reserve with an upper-body injury (minimum 3 games).

    # Vegas Golden Knights
    "Alex Pietrangelo": 0,       # Placed on LTIR (Hip); out long-term
    "Shea Theodore": 1.15,       # Inherits top PP unit and max deployment minutes
    

}