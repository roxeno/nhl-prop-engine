import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
from pathlib import Path

DATA_PATH = "../data/built/readytouse.csv"
df = pd.read_csv(DATA_PATH)
def show_top_n():
    """Horizontal bar chart of top players by expected lambda."""
    # Sort so the highest lambda is at the top
    df_top = df.sort_values("expectedLambda", ascending=False).head(25)
    
    # Reverse so Plotly plots the highest at the top of the y-axis
    df_top = df_top.iloc[::-1]

    fig = px.bar(
        df_top,
        x="expectedLambda",
        y="name",
        orientation="h",
        color="expectedLambda",
        color_continuous_scale="Blues",
        title=f"Top 25 Expected Shots on Goal (Tonight)",
        labels={"expectedLambda": "Expected Shots (λ)", "name": ""},
        hover_data={
            "opponent": True,
            "p_at_least_1": ":.1%",
            "p_at_least_2": ":.1%",
            "expectedLambda": ":.2f",
            "name": False,
        }
    )

    fig.update_layout(
        height=800,
        yaxis=dict(tickmode="linear"),
        margin=dict(l=150, r=20, t=50, b=50),
        coloraxis_showscale=False,
    )
    
    fig.show()

def show_top_5_distributions():
    """
    Creates an interactive chart showing the top 5 players' distributions.
    """
    # 1. Get the top 5 players by expectedLambda
    top_5 = df.sort_values("expectedLambda", ascending=False).head(5)

    # 2. Setup the figure
    fig = go.Figure()
    
    # We extend the labels to 7, plus the 8+ bucket
    labels = ["0", "1", "2", "3", "4", "5", "6", "7", "8+"]

    # 3. Add a trace (bar chart) for each player
    for _, row in top_5.iterrows():
        lam = row["expectedLambda"]
        name = row["name"]
        opp = row["opponent"]
        
        # Calculate P(exactly k)
        probs = [poisson.pmf(k, lam) for k in range(8)]
        # Calculate P(>= 5)
        prob_8_plus = poisson.sf(7, lam)

        probs.append(prob_8_plus)
        
        fig.add_trace(go.Bar(
            name=f"{name} (vs {opp})",
            x=labels,
            y=probs,
            text=[f"{p:.1%}" for p in probs],
            textposition="auto",
        ))

    # 4. Add dropdown menu to switch between players
    # We create a list of buttons, one for each player
    buttons = []
    
    # First button: Show all 5 at once
    buttons.append(dict(
        label="All Top 5",
        method="update",
        args=[{"visible": [True, True, True, True, True]},
              {"title": "Top 5 Players - Shot Distributions"}]
    ))

    # Individual player buttons
    for i, (_, row) in enumerate(top_5.iterrows()):
        visibility = [False] * 5
        visibility[i] = True # Only show this player
        
        buttons.append(dict(
            label=f"{row['name']}",
            method="update",
            args=[{"visible": visibility},
                  {"title": f"{row['name']} vs {row['opponent']} — λ = {row['expectedLambda']:.2f}"}]
        ))

    # 5. Update layout with the dropdown
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ],
        title="Top 5 Players - Shot Distributions",
        xaxis_title="Shots on Goal",
        yaxis_title="Probability",
        yaxis=dict(tickformat=".0%"),
        barmode="group", # Puts bars side-by-side when "All" is selected
        height=600,
    )

    fig.show()

def show_player_distribution(player_name: str):
    """Vertical bar chart of P(exactly k shots) for a single player."""
    row = df[df["name"] == player_name]
    
    if row.empty:
        print(f"Player '{player_name}' not found in the data.")
        return
        
    row = row.iloc[0]
    lam = row["expectedLambda"]
    opp = row["opponent"]
    
    # Calculate exactly P(X = k) for k=0 to 4
    probs = [poisson.pmf(k, lam) for k in range(5)]
    # Calculate P(X >= 5)
    prob_5_plus = 1 - sum(probs)
    probs.append(prob_5_plus)
    
    labels = ["0", "1", "2", "3", "4", "5+"]
    
    # Color the "most likely" bar differently
    max_idx = probs.index(max(probs))
    colors = ["#636EFA"] * 6
    colors[max_idx] = "#EF553B" # Highlight the most likely outcome

    fig = go.Figure(data=[
        go.Bar(
            x=labels, 
            y=probs, 
            marker_color=colors,
            text=[f"{p:.1%}" for p in probs],
            textposition="auto",
        )
    ])

    fig.update_layout(
        title=f"{player_name} vs {opp} — λ = {lam:.2f}",
        xaxis_title="Shots on Goal",
        yaxis_title="Probability",
        yaxis=dict(tickformat=".0%"),
        height=500,
    )

    fig.show()

def main():
    # Load the data
    df = pd.read_csv(DATA_PATH)

    # Show the board
    show_top_n()

    # Show the interactive Top 5 chart
    show_top_5_distributions()

    # Show a specific player's distribution
    # show_player_distribution("Nathan MacKinnon", df)

if __name__ == "__main__":
    main()