def create_runs_distribution_chart(df, team, phase=None):
    """Create comprehensive runs distribution analysis from scratch using Plotly"""
    import plotly.graph_objects as go
    
    # Filter data for batting team
    team_data = df[df['batting_team'] == team].copy()
    
    # Apply phase filter if specified
    if phase:
        team_data = team_data[team_data['phase'] == phase]
    
    # Check if we have data
    if len(team_data) == 0:
        return None
    
    # Calculate runs distribution statistics
    runs_counts = team_data['runs_off_bat'].value_counts().reset_index()
    runs_counts.columns = ['runs', 'count']
    runs_counts = runs_counts.sort_values('runs')
    
    # Calculate percentages
    total_balls = len(team_data)
    runs_counts['percentage'] = ((runs_counts['count'] / total_balls) * 100).round(1)
    
    # Calculate cumulative percentage
    runs_counts['cumulative_pct'] = runs_counts['percentage'].cumsum().round(1)
    
    # Create color mapping for different run types (Neon themed)
    color_map = {
        0: '#94a3b8',  # Gray (dots)
        1: '#4ade80',  # Green (singles)
        2: '#3b82f6',  # Blue (twos)
        3: '#f59e0b',  # Orange (threes)
        4: '#d946ef',  # Purple (fours)
        6: '#f43f5e',  # Red (sixes)
    }
    
    label_map = {
        0: 'Dot Balls', 1: 'Singles', 2: 'Twos', 
        3: 'Threes', 4: 'Fours', 6: 'Sixes'
    }
    
    runs_counts['color'] = runs_counts['runs'].map(lambda x: color_map.get(x, '#fbbf24'))
    runs_counts['label'] = runs_counts['runs'].map(lambda x: label_map.get(x, f'{int(x)} Runs'))
    
    # Calculate summary statistics
    total_runs = int(team_data['runs_off_bat'].sum())
    avg_runs_per_ball = round(total_runs / total_balls, 2) if total_balls > 0 else 0
    dots = int(len(team_data[team_data['runs_off_bat'] == 0]))
    boundaries = int(len(team_data[(team_data['runs_off_bat'] == 4) | (team_data['runs_off_bat'] == 6)]))
    dot_pct = round((dots / total_balls) * 100, 1) if total_balls > 0 else 0
    boundary_pct = round((boundaries / total_balls) * 100, 1) if total_balls > 0 else 0
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=runs_counts['label'],
        y=runs_counts['count'],
        text=[f"<b>{count}</b><br><span style='font-size:11px;color:#cbd5e1'>{pct}%</span>" for count, pct in zip(runs_counts['count'], runs_counts['percentage'])],
        textposition='auto',
        marker=dict(
            color=runs_counts['color'],
            line=dict(color='rgba(255,255,255,0.3)', width=1.5),
        ),
        hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata}%<extra></extra>",
        customdata=runs_counts['percentage']
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{team}</b><br><span style='font-size:13px;color:#94a3b8'>Total Runs: {total_runs} | Total Balls: {total_balls} | Avg: {avg_runs_per_ball}</span><br><span style='font-size:13px;color:#94a3b8'>Dots: {dot_pct}% | Boundaries: {boundary_pct}%</span>",
            font=dict(size=18, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            showgrid=False,
            title="",
            tickfont=dict(size=12, color='#e2e8f0', weight='bold')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            title="Number of Balls",
            tickfont=dict(size=11, color='#94a3b8')
        ),
        margin=dict(t=90, b=40, l=50, r=20),
        showlegend=False,
        height=400,
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.9)",
            font_size=13,
            font_family="Segoe UI"
        )
    )
    
    return fig

def create_strike_rate_comparison(df, phase=None):
    """Create strike rate comparison chart for top strikers across teams using Plotly"""
    import plotly.graph_objects as go
    if phase:
        data = df[df['phase'] == phase].copy()
    else:
        data = df.copy()
    
    striker_stats = data.groupby(['striker', 'batting_team']).agg({
        'runs_off_bat': 'sum',
        'ball': 'count'
    }).reset_index()
    
    striker_stats = striker_stats[striker_stats['ball'] >= 50]
    striker_stats['strike_rate'] = (striker_stats['runs_off_bat'] / striker_stats['ball'] * 100).round(2)
    striker_stats = striker_stats.sort_values('strike_rate', ascending=True).tail(15)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=striker_stats['strike_rate'],
        y=striker_stats['striker'],
        orientation='h',
        text=[f"<b>{sr}</b>" for sr in striker_stats['strike_rate']],
        textposition='auto',
        marker=dict(
            color=striker_stats['strike_rate'],
            colorscale='Viridis',
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Team: %{customdata[0]}<br>Strike Rate: %{x}<br>Runs: %{customdata[1]}<br>Balls: %{customdata[2]}<extra></extra>",
        customdata=striker_stats[['batting_team', 'runs_off_bat', 'ball']]
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Top 15 Strikers by Strike Rate (min 50 balls)</b>",
            font=dict(size=18, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            title="Strike Rate",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(size=11, color='#94a3b8')
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(size=12, color='#e2e8f0', weight='bold')
        ),
        margin=dict(t=70, b=40, l=120, r=40),
        showlegend=False,
        height=500,
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
    )
    return fig

def create_boundary_percentage_chart(df, teams, phase=None):
    """Create comprehensive boundary and dot ball analysis using Plotly"""
    import plotly.graph_objects as go
    import pandas as pd
    results = []
    
    for team in teams:
        team_data = df[df['batting_team'] == team].copy()
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        total_balls = len(team_data)
        if total_balls == 0:
            continue
        
        fours = len(team_data[team_data['runs_off_bat'] == 4])
        sixes = len(team_data[team_data['runs_off_bat'] == 6])
        dots = len(team_data[team_data['runs_off_bat'] == 0])
        singles = len(team_data[team_data['runs_off_bat'] == 1])
        twos = len(team_data[team_data['runs_off_bat'] == 2])
        
        results.append({'team': team, 'category': 'Fours (4s)', 'percentage': round((fours/total_balls)*100, 1)})
        results.append({'team': team, 'category': 'Sixes (6s)', 'percentage': round((sixes/total_balls)*100, 1)})
        results.append({'team': team, 'category': 'Dot Balls', 'percentage': round((dots/total_balls)*100, 1)})
        results.append({'team': team, 'category': 'Singles (1s)', 'percentage': round((singles/total_balls)*100, 1)})
        results.append({'team': team, 'category': 'Twos (2s)', 'percentage': round((twos/total_balls)*100, 1)})
    
    if len(results) == 0:
        return None
        
    chart_df = pd.DataFrame(results)
    fig = go.Figure()
    
    categories = ['Dot Balls', 'Singles (1s)', 'Twos (2s)', 'Fours (4s)', 'Sixes (6s)']
    colors = ['#3b82f6', '#f43f5e']
    
    for idx, team in enumerate(teams):
        team_df = chart_df[chart_df['team'] == team]
        if len(team_df) == 0: continue
        
        team_df = team_df.set_index('category').reindex(categories).reset_index()
        
        fig.add_trace(go.Bar(
            name=team,
            x=team_df['category'],
            y=team_df['percentage'],
            text=[f"<b>{pct}%</b>" for pct in team_df['percentage']],
            textposition='auto',
            marker=dict(
                color=colors[idx % len(colors)],
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            hovertemplate="<b>%{x}</b><br>Team: " + team + "<br>Percentage: %{y}%<extra></extra>"
        ))
        
    fig.update_layout(
        barmode='group',
        title=dict(
            text="<b>Boundary & Dot Ball Analysis - Team Comparison</b>",
            font=dict(size=18, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(size=12, color='#e2e8f0', weight='bold')
        ),
        yaxis=dict(
            title="Percentage of Balls (%)",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(size=11, color='#94a3b8')
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=100, b=40, l=50, r=20),
        height=400,
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
    )
    return fig

def create_runs_over_progression(df, team, phase=None):
    """Create runs progression over overs using Plotly"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    team_data = df[df['batting_team'] == team].copy()
    if phase:
        team_data = team_data[team_data['phase'] == phase]
    
    over_runs = team_data.groupby('over')['runs_off_bat'].sum().reset_index()
    over_runs['cumulative_runs'] = over_runs['runs_off_bat'].cumsum()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=over_runs['over'],
            y=over_runs['runs_off_bat'],
            name="Runs per Over",
            marker_color='rgba(236, 72, 153, 0.5)',
            marker_line_color='rgba(236, 72, 153, 1)',
            marker_line_width=1.5,
            opacity=0.8
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(
            x=over_runs['over'],
            y=over_runs['cumulative_runs'],
            name="Cumulative Runs",
            mode='lines+markers',
            line=dict(color='#60a5fa', width=3),
            marker=dict(size=8, color='#3b82f6', line=dict(color='white', width=1)),
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{team} - Runs Progression Over Overs</b>",
            font=dict(size=16, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            title="Over",
            showgrid=False,
            tickmode='linear',
            tick0=0, dtick=1,
            tickfont=dict(size=11, color='#94a3b8')
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=80, b=40, l=40, r=40),
        height=400,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
    )
    
    fig.update_yaxes(title_text="Runs per Over", showgrid=False, secondary_y=False, tickfont=dict(color='#94a3b8'))
    fig.update_yaxes(title_text="Cumulative Runs", showgrid=True, gridcolor='rgba(255,255,255,0.05)', secondary_y=True, tickfont=dict(color='#60a5fa'))
    
    return fig

def create_wicket_timeline(df, bowling_team, phase=None):
    """Create wicket fall timeline using Plotly"""
    import plotly.graph_objects as go
    
    team_data = df[df['bowling_team'] == bowling_team].copy()
    if phase:
        team_data = team_data[team_data['phase'] == phase]
    
    wickets = team_data[team_data['is_wicket'] == 1].copy()
    if wickets.empty:
        return None
        
    wickets['wicket_num'] = range(1, len(wickets) + 1)
    
    fig = go.Figure()
    
    for w_type in wickets['wicket_type'].unique():
        w_data = wickets[wickets['wicket_type'] == w_type]
        fig.add_trace(go.Scatter(
            x=w_data['over'],
            y=w_data['wicket_num'],
            mode='markers',
            name=str(w_type),
            marker=dict(
                size=16,
                line=dict(color='rgba(255,255,255,0.8)', width=1.5),
                symbol='circle'
            ),
            text=[f"Striker: {b}<br>Bowler: {bw}<br>Over: {o}" for b, bw, o in zip(w_data['striker'], w_data['bowler'], w_data['over'])],
            hovertemplate="<b>%{text}</b><br>Dismissal: " + str(w_type) + "<extra></extra>"
        ))
        
    fig.update_layout(
        title=dict(
            text=f"<b>{bowling_team} - Wicket Fall Timeline</b>",
            font=dict(size=16, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            title="Over",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickmode='linear',
            tick0=0, dtick=2,
            tickfont=dict(size=11, color='#94a3b8')
        ),
        yaxis=dict(
            title="Wicket Number",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            autorange="reversed",
            tickfont=dict(size=11, color='#94a3b8'),
            tickmode='linear',
            tick0=1, dtick=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=80, b=40, l=40, r=40),
        height=400,
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
    )
    return fig

def create_bowler_economy_chart(df, team, phase=None):
    """Create comprehensive bowler economy rate analysis using Plotly"""
    import plotly.graph_objects as go
    import pandas as pd

    team_data = df[df['bowling_team'] == team].copy()
    if phase:
        team_data = team_data[team_data['phase'] == phase]

    if len(team_data) == 0:
        return None

    bowler_stats = team_data.groupby('bowler').agg({
        'runs_off_bat': 'sum',
        'extras': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()

    bowler_stats = bowler_stats[bowler_stats['ball'] >= 18].copy()
    if len(bowler_stats) == 0:
        return None

    bowler_stats['overs'] = (bowler_stats['ball'] / 6).round(1)
    bowler_stats['total_runs'] = bowler_stats['runs_off_bat'] + bowler_stats['extras']
    bowler_stats['economy'] = (bowler_stats['total_runs'] / bowler_stats['overs']).round(2)
    bowler_stats = bowler_stats.sort_values('economy', ascending=True).head(10)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bowler_stats['economy'],
        y=bowler_stats['bowler'],
        orientation='h',
        text=[f"<b>{econ}</b>" for econ in bowler_stats['economy']],
        textposition='auto',
        marker=dict(
            color=bowler_stats['economy'],
            colorscale='Emerald',
            reversescale=True,
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Economy: %{x}<br>Overs: %{customdata[0]}<br>Wickets: %{customdata[1]}<extra></extra>",
        customdata=bowler_stats[['overs', 'is_wicket']]
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>{team} - Top Bowler Economy Profiles</b>",
            font=dict(size=16, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Segoe UI'),
        xaxis=dict(
            title="Economy Rate (Runs/Over)",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(size=11, color='#94a3b8')
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=12, color='#e2e8f0', weight='bold')),
        margin=dict(t=70, b=40, l=120, r=40),
        height=400,
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
    )
    return fig
