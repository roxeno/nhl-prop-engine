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

def get_pp_impact_fig(df, n=20):
    df_top = df.sort_values("expectedLambda", ascending=False).head(n)
    df_top = df_top.iloc[::-1] 

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_top['name'], x=df_top['lambda_5v5'],
        name='5v5', orientation='h', marker=dict(color='#1f77b4') 
    ))
    fig.add_trace(go.Bar(
        y=df_top['name'], x=df_top['lambda_pp'],
        name='Power Play', orientation='h', marker=dict(color='#ff7f0e') 
    ))

    fig.update_layout(
        barmode='stack', 
        title=f"Top {n}: 5v5 vs PP",
        xaxis_title="Expected Shots",
        height=380,
        margin=dict(l=100, r=20, t=50, b=50),
        legend=dict(x=0.5, y=1.1, orientation="h")
    )
    return fig

def get_hd_impact_fig(df, n=40):
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
        title=f"Top {n}: Volume vs High-Danger",
        trendline="ols" # <-- Adds a nice trendline showing the correlation
    )

    fig.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color='DarkSlateGrey')),
        selector=dict(mode='markers+text') # Only applies to the scatter points, not the trendline
    )

    # Add crosshairs
    fig.add_hline(y=df_top['expectedLambda_hd'].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=df_top['expectedLambda'].median(), line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        xaxis_title="Expected Total Shots (λ)",
        yaxis_title="Expected High-Danger Shots (λ)",
        height=380,
        margin=dict(l=50, r=20, t=50, b=50),
        yaxis=dict(range=[0, df_top['expectedLambda_hd'].max() * 1.1]), # <-- Force Y axis to start at 0
        xaxis=dict(range=[df_top['expectedLambda'].min() * 0.9, df_top['expectedLambda'].max() * 1.1]) # <-- Add padding to X
    )
    
    return fig