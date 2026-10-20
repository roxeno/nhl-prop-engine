import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
import pandas as pd


def get_top_n_fig(df, n=25):
    """Horizontal bar chart of top players by expected lambda, showing goalie matchup."""
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)
    df_top = df_top.iloc[::-1]

    fig = px.bar(
        df_top,
        x="expectedLambda",
        y="name",
        orientation="h",
        color="expectedLambda",
        color_continuous_scale="Blues",
        title=f"Top {n} Expected Shots on Goal (Tonight)",
        labels={"expectedLambda": "Expected Shots (λ)", "name": ""},
        hover_data={
            "opponent": True,
            "sv_pct": ":.3f", 
            "expectedLambda_hd": ":.2f", # <-- NEW: Shows High Danger Lambda
            "p_at_least_1": ":.1%",
            "p_at_least_2": ":.1%",
            "name": False,
        }
    )

    fig.update_layout(
        height=800,
        yaxis=dict(
            tickmode="linear",
            tickfont=dict(size=10) # <-- Make names readable on mobile
        ),
        margin=dict(l=100, r=20, t=50, b=50), # Reduce left margin
        coloraxis_showscale=False,
    )
    
    return fig

def get_top_5_distributions(df, n=5):
    """Interactive chart showing the top 5 players' distributions."""
    top_5 = df.sort_values("expectedLambda", ascending=False).head(n)
    fig = go.Figure()
    
    labels = ["0", "1", "2", "3", "4", "5", "6", "7", "8+"]

    for _, row in top_5.iterrows():
        lam = row["expectedLambda"]
        name = row["name"]
        opp = row["opponent"]
        sv = row["sv_pct"]
        hd_lam = row["expectedLambda_hd"] # <-- NEW: Pull HD Lambda
        
        probs = [poisson.pmf(k, lam) for k in range(8)]
        probs.append(poisson.sf(7, lam)) 
        
        fig.add_trace(go.Bar(
            name=f"{name} (vs {opp} - {sv:.3f} SV%)",
            x=labels,
            y=probs,
            text=[f"{p:.1%}" for p in probs],
            textposition="auto",
            customdata=[[hd_lam]] * len(labels), # <-- NEW: Pass HD Lambda to hover
            hovertemplate="%{x} shots: %{y:.1%}<br>HD Lambda: %{customdata[0]:.2f}<extra></extra>" # <-- NEW: Custom hover
        ))

    # Dropdown menu
    buttons = [dict(
        label="All Top 5",
        method="update",
        args=[{"visible": [True, True, True, True, True]},
              {"title": "Top 5 Players - Shot Distributions"}]
    )]

    for i, (_, row) in enumerate(top_5.iterrows()):
        visibility = [False] * 5
        visibility[i] = True 
        
        buttons.append(dict(
            label=f"{row['name']}",
            method="update",
            args=[{"visible": visibility},
                  {"title": f"{row['name']} vs {row['opponent']} ({row['sv_pct']:.3f} SV%) — λ = {row['expectedLambda']:.2f} (HD: {row['expectedLambda_hd']:.2f})"}]
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons, direction="down",
            pad={"r": 10, "t": 10}, showactive=True,
            x=0.0, xanchor="left", y=1.15, yanchor="top"
        )],
        title="Top 5 Players - Shot Distributions",
        xaxis_title="Shots on Goal",
        yaxis_title="Probability",
        yaxis=dict(tickformat=".0%"),
        barmode="group",
        height=600,
    )

    return fig

def get_pp_impact_fig(df, n=20):
    """Compares 5v5 Expected Shots vs Power Play Expected Shots."""
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)
    df_top = df_top.iloc[::-1] 

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_top['name'],
        x=df_top['lambda_5v5'],
        name='5v5 Expected Shots',
        orientation='h',
        marker=dict(color='#1f77b4') 
    ))

    fig.add_trace(go.Bar(
        y=df_top['name'],
        x=df_top['lambda_pp'],
        name='PP Expected Shots',
        orientation='h',
        marker=dict(color='#ff7f0e') 
    ))

    fig.update_layout(
        barmode='stack', 
        title=f"Top {n} Players: 5v5 vs Power Play Expected Shots (λ)",
        xaxis_title="Expected Shots",
        yaxis_title="",
        height=800,
        margin=dict(l=150, r=20, t=50, b=50),
        legend=dict(x=0.7, y=1.1, orientation="h")
    )

    return fig

def get_hd_impact_fig(df, n=40):
    """Scatter plot comparing Total Expected Shots vs High-Danger Expected Shots."""
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)

    fig = px.scatter(
        df_top,
        x="expectedLambda",
        y="expectedLambda_hd",
        text="name",
        color="expectedLambda_hd",
        color_continuous_scale="Reds",
        size="expectedLambda", 
        hover_data={
            "name": True,
            "opponent": True,
            "sv_pct": ":.3f",
            "expectedLambda": ":.2f",
            "expectedLambda_hd": ":.2f",
        },
        title=f"Top {n} Players: Total Volume vs. High-Danger Shots"
    )

    fig.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color='DarkSlateGrey'))
    )

    fig.add_hline(y=df_top['expectedLambda_hd'].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=df_top['expectedLambda'].median(), line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        xaxis_title="Expected Total Shots (λ)",
        yaxis_title="Expected High-Danger Shots (λ)",
        height=700,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    return fig

def show_player_distribution(df, player_name: str):
    """Vertical bar chart of P(exactly k shots) for a single player."""
    row = df[df["name"] == player_name]
    
    if row.empty:
        print(f"Player '{player_name}' not found in the data.")
        return
        
    row = row.iloc[0]
    lam = row["expectedLambda"]
    opp = row["opponent"]
    sv = row["sv_pct"]
    hd_lam = row["expectedLambda_hd"]
    
    probs = [poisson.pmf(k, lam) for k in range(5)]
    prob_5_plus = poisson.sf(4, lam) 
    probs.append(prob_5_plus)
    
    labels = ["0", "1", "2", "3", "4", "5+"]
    
    max_idx = probs.index(max(probs))
    colors = ["#636EFA"] * 6
    colors[max_idx] = "#EF553B" 

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
        title=f"{player_name} vs {opp} ({sv:.3f} SV%) — λ = {lam:.2f} (HD: {hd_lam:.2f})",
        xaxis_title="Shots on Goal",
        yaxis_title="Probability",
        yaxis=dict(tickformat=".0%"),
        height=500,
    )

    return fig
