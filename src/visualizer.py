import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
import pandas as pd

def get_top_n_fig(df, n=25):
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)
    df_top = df_top.iloc[::-1]

    fig = px.bar(
        df_top,
        x="expectedLambda",
        y="name",
        orientation="h",
        color="expectedLambda",
        color_continuous_scale="Blues",
        title=f"Top {n} Expected Shots on Goal",
        labels={"expectedLambda": "Expected Shots (λ)", "name": ""},
        hover_data={
            "opponent": True,
            "sv_pct": ":.3f", 
            "expectedLambda_hd": ":.2f", 
            "p_at_least_1": ":.1%",
            "p_at_least_2": ":.1%",
            "name": False,
        }
    )

    fig.update_layout(
        height=800,
        yaxis=dict(tickmode="linear", tickfont=dict(size=10)),
        margin=dict(l=80, r=20, t=50, b=50),
        coloraxis_showscale=False,
    )
    return fig

def get_hd_impact_fig(df, n=40):
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)

    fig = px.scatter(
        df_top, 
        x="expectedLambda", 
        y="expectedLambda_hd", 
        # text="name",  <-- REMOVE THIS LINE (It causes the overlap on mobile)
        color="expectedLambda_hd", 
        color_continuous_scale="Reds",
        size="expectedLambda", 
        hover_name="name", # <-- Shows the name at the top of the hover box
        hover_data={
            "opponent": True, 
            "sv_pct": ":.3f",
            "expectedLambda": ":.2f", 
            "expectedLambda_hd": ":.2f",
        },
        title=f"Top {n}: Volume vs High-Danger",
        trendline="ols" 
    )

    # Make the bubbles slightly larger and add a border so they pop
    fig.update_traces(
        marker=dict(line=dict(width=1, color='DarkSlateGrey'), sizemin=8),
        selector=dict(mode='markers') # Only apply to the scatter points, not the trendline
    )

    # Add crosshairs (median lines)
    fig.add_hline(y=df_top['expectedLambda_hd'].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=df_top['expectedLambda'].median(), line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        xaxis_title="Expected Total Shots (λ)",
        yaxis_title="Expected High-Danger Shots (λ)",
        height=450, # Increase height slightly for mobile scrolling
        margin=dict(l=40, r=20, t=50, b=40), # Tighter margins for mobile
        yaxis=dict(range=[0, df_top['expectedLambda_hd'].max() * 1.2]), 
        xaxis=dict(range=[df_top['expectedLambda'].min() * 0.9, df_top['expectedLambda'].max() * 1.1])
    )
    
    return fig