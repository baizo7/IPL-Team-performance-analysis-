"""
IPL Team Performance Dashboard
A Streamlit app for analyzing and comparing IPL team performance.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path

from data_processor import IPLDataProcessor
from analysis import PhaseAnalyzer, MatchupAnalyzer, PerformanceMetrics


# Page configuration
st.set_page_config(
    page_title="IPL Team Performance Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def load_data(use_sample=True):
    """Load and cache IPL data."""
    processor = IPLDataProcessor('data')
    
    if use_sample:
        df = processor.create_sample_data()
        st.info("📊 Using sample data. Download real IPL data from Cricsheet.org and place CSV files in the 'data' folder.")
    else:
        try:
            df = processor.load_csv_data()
            st.success(f"✅ Loaded {len(df)} ball-by-ball records from CSV files")
        except FileNotFoundError:
            st.warning("⚠️ No data files found. Falling back to sample data.")
            df = processor.create_sample_data()
    
    return df, processor


def plot_phase_comparison(comparison_data, team1, team2):
    """Create phase comparison chart."""
    combined_df = comparison_data['combined']
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Run Rate by Phase', 'Boundaries by Phase', 
                       'Wickets Lost by Phase', 'Strike Rate by Phase'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Run Rate
    for team in [team1, team2]:
        team_data = combined_df[combined_df['team'] == team]
        fig.add_trace(
            go.Bar(name=team, x=team_data['phase'], y=team_data['run_rate'],
                  text=team_data['run_rate'], textposition='auto'),
            row=1, col=1
        )
    
    # Boundaries
    for team in [team1, team2]:
        team_data = combined_df[combined_df['team'] == team]
        fig.add_trace(
            go.Bar(name=team, x=team_data['phase'], y=team_data['boundaries'],
                  text=team_data['boundaries'], textposition='auto', showlegend=False),
            row=1, col=2
        )
    
    # Wickets
    for team in [team1, team2]:
        team_data = combined_df[combined_df['team'] == team]
        fig.add_trace(
            go.Bar(name=team, x=team_data['phase'], y=team_data['total_wickets'],
                  text=team_data['total_wickets'], textposition='auto', showlegend=False),
            row=2, col=1
        )
    
    # Strike Rate
    for team in [team1, team2]:
        team_data = combined_df[combined_df['team'] == team]
        fig.add_trace(
            go.Bar(name=team, x=team_data['phase'], y=team_data['strike_rate'],
                  text=team_data['strike_rate'], textposition='auto', showlegend=False),
            row=2, col=2
        )
    
    fig.update_layout(height=700, showlegend=True, title_text=f"Phase Analysis: {team1} vs {team2}")
    fig.update_xaxes(categoryorder='array', categoryarray=['Powerplay', 'Middle', 'Death'])
    
    return fig


def plot_matchup_heatmap(heatmap_data, team_name, metric='strike_rate'):
    """Create matchup heatmap."""
    if heatmap_data.empty:
        st.warning(f"No matchup data available for {team_name}")
        return None
    
    title = f"{team_name} - Batter vs Bowler Type "
    title += "Strike Rate" if metric == 'strike_rate' else "Dismissal Rate"
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Bowler Type", y="Batter", color=metric.replace('_', ' ').title()),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='RdYlGn' if metric == 'strike_rate' else 'RdYlGn_r',
        aspect="auto",
        title=title
    )
    
    fig.update_layout(height=500)
    
    return fig


def plot_phase_distribution(team_data, team_name):
    """Create phase-wise run distribution."""
    phase_data = team_data.groupby('phase').agg({
        'runs': 'sum',
        'extras': 'sum'
    }).reset_index()
    
    phase_data['total'] = phase_data['runs'] + phase_data['extras']
    
    fig = px.pie(
        phase_data,
        values='total',
        names='phase',
        title=f'{team_name} - Runs Distribution by Phase',
        color='phase',
        color_discrete_map={'Powerplay': '#636EFA', 'Middle': '#EF553B', 'Death': '#00CC96'},
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label+value')
    
    return fig


def main():
    """Main application."""
    
    # Header
    st.markdown('<p class="main-header">🏏 IPL Team Performance Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ Dashboard Controls")
    
    # Data source selection
    use_sample = st.sidebar.checkbox("Use Sample Data", value=True, 
                                     help="Uncheck to use real data from 'data' folder")
    
    # Load data
    df, processor = load_data(use_sample)
    
    # Team selection
    st.sidebar.subheader("Select Teams to Compare")
    available_teams = processor.get_available_teams()
    
    if len(available_teams) < 2:
        st.error("Not enough teams in the dataset. Please load proper data.")
        return
    
    team1 = st.sidebar.selectbox("Team 1", available_teams, index=0)
    team2 = st.sidebar.selectbox("Team 2", available_teams, 
                                  index=min(1, len(available_teams)-1))
    
    if team1 == team2:
        st.warning("⚠️ Please select two different teams for comparison")
        return
    
    # Initialize analyzers
    phase_analyzer = PhaseAnalyzer(df)
    matchup_analyzer = MatchupAnalyzer(df)
    metrics = PerformanceMetrics(df)
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Phase Analysis", "🔥 Matchup Analysis", 
                                       "🏆 Team Summary", "📈 Detailed Stats"])
    
    with tab1:
        st.header(f"Phase Analysis: {team1} vs {team2}")
        
        # Get comparison data
        comparison = phase_analyzer.compare_teams(team1, team2)
        
        if comparison['combined'].empty:
            st.warning("No data available for phase analysis")
        else:
            # Plot comparison
            fig = plot_phase_comparison(comparison, team1, team2)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data tables
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{team1} Phase Metrics")
                st.dataframe(comparison['team1'].drop('team', axis=1), use_container_width=True)
                
                # Distribution chart
                team1_data = df[df['batting_team'] == team1]
                fig1 = plot_phase_distribution(team1_data, team1)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.subheader(f"{team2} Phase Metrics")
                st.dataframe(comparison['team2'].drop('team', axis=1), use_container_width=True)
                
                # Distribution chart
                team2_data = df[df['batting_team'] == team2]
                fig2 = plot_phase_distribution(team2_data, team2)
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.header("Batter vs Bowler Type Matchups")
        
        # Metric selection
        metric_choice = st.radio("Select Metric", 
                                 ["Strike Rate", "Dismissal Rate"],
                                 horizontal=True)
        metric = 'strike_rate' if metric_choice == "Strike Rate" else 'dismissal_rate'
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"{team1} Matchups")
            heatmap1 = matchup_analyzer.create_heatmap_data(team1, metric)
            fig1 = plot_matchup_heatmap(heatmap1, team1, metric)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
            
            # Top matchups
            st.subheader(f"Top Performing Matchups - {team1}")
            top_matchups1 = matchup_analyzer.get_top_matchups(team1, n=10)
            if not top_matchups1.empty:
                st.dataframe(top_matchups1, use_container_width=True)
        
        with col2:
            st.subheader(f"{team2} Matchups")
            heatmap2 = matchup_analyzer.create_heatmap_data(team2, metric)
            fig2 = plot_matchup_heatmap(heatmap2, team2, metric)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            
            # Top matchups
            st.subheader(f"Top Performing Matchups - {team2}")
            top_matchups2 = matchup_analyzer.get_top_matchups(team2, n=10)
            if not top_matchups2.empty:
                st.dataframe(top_matchups2, use_container_width=True)
    
    with tab3:
        st.header("Team Performance Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"{team1} Overview")
            summary1 = metrics.team_summary(team1)
            
            if summary1:
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("Total Runs", f"{summary1['total_runs']:,}")
                metrics_col2.metric("Matches", summary1['total_matches'])
                metrics_col3.metric("Run Rate", summary1['overall_run_rate'])
                
                metrics_col4, metrics_col5, metrics_col6 = st.columns(3)
                metrics_col4.metric("Strike Rate", summary1['overall_strike_rate'])
                metrics_col5.metric("Wickets Lost", summary1['total_wickets'])
                metrics_col6.metric("Avg/Match", summary1['avg_runs_per_match'])
            
            st.subheader(f"Top Batters - {team1}")
            top_batters1 = metrics.top_batters(team1, n=5)
            if not top_batters1.empty:
                st.dataframe(top_batters1, use_container_width=True)
        
        with col2:
            st.subheader(f"{team2} Overview")
            summary2 = metrics.team_summary(team2)
            
            if summary2:
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("Total Runs", f"{summary2['total_runs']:,}")
                metrics_col2.metric("Matches", summary2['total_matches'])
                metrics_col3.metric("Run Rate", summary2['overall_run_rate'])
                
                metrics_col4, metrics_col5, metrics_col6 = st.columns(3)
                metrics_col4.metric("Strike Rate", summary2['overall_strike_rate'])
                metrics_col5.metric("Wickets Lost", summary2['total_wickets'])
                metrics_col6.metric("Avg/Match", summary2['avg_runs_per_match'])
            
            st.subheader(f"Top Batters - {team2}")
            top_batters2 = metrics.top_batters(team2, n=5)
            if not top_batters2.empty:
                st.dataframe(top_batters2, use_container_width=True)
    
    with tab4:
        st.header("Detailed Statistics")
        
        # Team data selector
        selected_team = st.selectbox("Select Team for Detailed View", [team1, team2])
        
        team_data = df[df['batting_team'] == selected_team]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Runs Distribution")
            runs_dist = team_data['runs'].value_counts().sort_index()
            fig_runs = px.bar(x=runs_dist.index, y=runs_dist.values,
                             labels={'x': 'Runs', 'y': 'Frequency'},
                             title=f'{selected_team} - Runs per Ball Distribution')
            st.plotly_chart(fig_runs, use_container_width=True)
        
        with col2:
            st.subheader("Over-by-Over Analysis")
            over_analysis = team_data.groupby('over').agg({
                'runs': 'sum',
                'extras': 'sum',
                'is_wicket': 'sum'
            }).reset_index()
            over_analysis['total_runs'] = over_analysis['runs'] + over_analysis['extras']
            
            fig_over = go.Figure()
            fig_over.add_trace(go.Scatter(x=over_analysis['over'], 
                                         y=over_analysis['total_runs'],
                                         mode='lines+markers',
                                         name='Runs',
                                         line=dict(color='#636EFA', width=3)))
            fig_over.update_layout(title=f'{selected_team} - Runs per Over',
                                  xaxis_title='Over',
                                  yaxis_title='Total Runs')
            st.plotly_chart(fig_over, use_container_width=True)
        
        # Full matchup data
        st.subheader("Complete Matchup Data")
        full_matchups = matchup_analyzer.calculate_batter_vs_bowler_type(team_name=selected_team)
        if not full_matchups.empty:
            st.dataframe(full_matchups.sort_values('strike_rate', ascending=False), 
                        use_container_width=True)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **About this Dashboard**
    
    This dashboard analyzes IPL team performance across:
    - Phase Analysis (Powerplay, Middle, Death)
    - Batter vs Bowler Type Matchups
    - Team Summaries
    - Detailed Statistics
    
    **Data Source:** Cricsheet.org
    """)


if __name__ == "__main__":
    main()
