import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import uuid
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. Data Loading and Cleaning
# -----------------------------------------------------------------------------

@st.cache_data
def load_data():
    """Load and clean IPL data"""
    path = "ipl_data"
    csv_file = "all_ipl_matches.csv"
    
    # Check if processed file exists
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        # Logic to load from folder or create sample
        if not os.path.exists(path):
            # Create sample data (simplified for app demo if data missing)
            teams = ['Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore', 
                     'Kolkata Knight Riders', 'Delhi Capitals', 'Rajasthan Royals', 
                     'Punjab Kings', 'Gujarat Titans', 'Lucknow Super Giants', 'Sunrisers Hyderabad']
            
            # ... (Sample generation logic could go here, but assuming data exists or CSV exists based on notebook usage)
            # For the app, let's assume the user has run the notebook and generated the CSV, 
            # or we'll use the sample generation if strictly needed. 
            # To keep it robust, I'll include a minimal sample generator if file missing.
            return create_sample_data()
            
        else:
            all_files = glob.glob(os.path.join(path, "*.csv"))
            if not all_files:
                return create_sample_data()
                
            df_list = []
            for filename in all_files:
                try:
                    df = pd.read_csv(filename, index_col=None, header=0, on_bad_lines='skip', encoding='utf-8')
                    if not df.empty:
                        df_list.append(df)
                except:
                    continue
            final_df = pd.concat(df_list, axis=0, ignore_index=True)
            df = final_df

    return clean_data(df)

def create_sample_data():
    # Fallback sample data generator
    teams = ['Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore', 'Kolkata Knight Riders']
    n_records = 1000
    df = pd.DataFrame({
        'match_id': np.repeat(range(1, 11), 100),
        'batting_team': np.random.choice(teams, n_records),
        'bowling_team': np.random.choice(teams, n_records),
        'ball': np.tile(np.arange(0.1, 20.1, 0.1), n_records // 200 + 1)[:n_records],
        'runs_off_bat': np.random.choice([0, 1, 4, 6], n_records),
        'extras': 0,
        'wicket_type': np.random.choice([None, 'caught'], n_records, p=[0.95, 0.05]),
        'batter': 'Sample Batter',
        'bowler': 'Sample Bowler'
    })
    return clean_data(df)

def clean_data(df):
    df = df.copy()
    
    # Column mapping
    column_mappings = {
        'runs_off_bat': ['runs_off_bat', 'batsman_runs', 'runs_scored'],
        'extras': ['extras', 'extra_runs'],
        'wicket_type': ['wicket_type', 'dismissal_kind', 'wicket_kind'],
        'batter': ['batter', 'batsman', 'striker'],
        'bowler': ['bowler', 'bowler_name'],
        'ball': ['ball', 'over_ball'],
        'batting_team': ['batting_team', 'team'],
        'bowling_team': ['bowling_team', 'opponent']
    }
    
    for standard_name, variations in column_mappings.items():
        for var in variations:
            if var in df.columns and standard_name not in df.columns:
                df.rename(columns={var: standard_name}, inplace=True)
                break
                
    # Basic columns
    if 'ball' in df.columns:
        df['ball'] = pd.to_numeric(df['ball'], errors='coerce').fillna(0)
        df['over'] = df['ball'].astype(int) + 1
    else:
        df['over'] = 1
        
    if 'runs_off_bat' in df.columns:
        df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
        df['total_runs'] = df['runs_off_bat'] + pd.to_numeric(df.get('extras', 0), errors='coerce').fillna(0)
    else:
        df['total_runs'] = 0
        
    # Phase
    df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21], labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)'])
    
    # Wicket
    if 'wicket_type' in df.columns:
        df['is_wicket'] = df['wicket_type'].notna().astype(int)
    else:
        df['is_wicket'] = 0
        
    # Bowler Type
    if 'bowler' in df.columns:
        def get_bowler_type(bowler_name):
            if pd.isna(bowler_name): return 'Unknown'
            name = str(bowler_name).lower()
            
            left_arm_pacers = ['boult', 'arshdeep', 'natarajan', 'mustafizur', 'curran', 'starc', 'afridi', 'khaleel', 'jansen', 'behrendorff', 'yash dayal', 'mohsin khan', 'kotian', 'nandre burger', 'mcclenaghan', 'faulkner', 'johnson', 'zaheer', 'nehra', 'irfan pathan', 'r p singh', 'unadkat', 'cottrell', 'mills', 'udana', 'sakariya', 'left-arm fast', 'left-arm medium']
            left_arm_wrist = ['kuldeep yadav', 'noor ahmad', 'tabraiz shamsi', 'chinaman']
            left_arm_orthodox = ['jadeja', 'axar', 'krunal', 'shahbaz', 'santner', 'shakib', 'sai kishore', 'harpreet brar', 'abhishek sharma', 'nadeem', 'imad wasim', 'left-arm orthodox']
            right_arm_leg = ['rashid', 'chahal', 'bishnoi', 'hasaranga', 'zampa', 'mishra', 'rahul chahar', 'markande', 'chawla', 'karn sharma', 'gopal', 'tahir', 'badree', 'murugan ashwin', 'legbreak', 'leg spin']
            right_arm_off = ['ashwin', 'narine', 'chakravarthy', 'theekshana', 'livingstone', 'maxwell', 'moeen', 'gowtham', 'sundar', 'harbhajan', 'nabi', 'rana', 'hooda', 'parag', 'off break', 'off spin']
            
            if any(p in name for p in left_arm_pacers): return 'Left-Arm Pace'
            elif any(p in name for p in left_arm_wrist): return 'Left-Arm Wrist Spin'
            elif any(p in name for p in left_arm_orthodox): return 'Left-Arm Orthodox'
            elif any(p in name for p in right_arm_leg): return 'Right-Arm Leg Spin'
            elif any(p in name for p in right_arm_off): return 'Right-Arm Off Spin'
            else: return 'Right-Arm Pace'

        df['bowler_type'] = df['bowler'].apply(get_bowler_type)
    else:
        df['bowler_type'] = 'Unknown'
        
    # Fill NaNs
    for col in ['batting_team', 'bowling_team', 'batter', 'bowler']:
        if col in df.columns: df[col] = df[col].fillna('Unknown')
        
    return df

# -----------------------------------------------------------------------------
# 2. Analysis Functions
# -----------------------------------------------------------------------------

def calculate_run_rate_by_phase(df, team):
    team_data = df[df['batting_team'] == team]
    phase_stats = team_data.groupby('phase', observed=False).agg({
        'total_runs': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()
    phase_stats['run_rate'] = (phase_stats['total_runs'] / phase_stats['ball']) * 6
    phase_stats['wickets'] = phase_stats['is_wicket']
    phase_stats['avg_runs_per_ball'] = phase_stats['total_runs'] / phase_stats['ball']
    return phase_stats

def calculate_player_matchup(df, player, bowler_type):
    player_data = df[(df['batter'] == player) & (df['bowler_type'] == bowler_type)]
    if len(player_data) == 0: return None
    
    balls = len(player_data)
    runs = int(player_data['runs_off_bat'].sum())
    dismissals = int(player_data['is_wicket'].sum())
    
    return {
        'balls_faced': int(balls),
        'runs_scored': runs,
        'dismissals': dismissals,
        'strike_rate': float((runs / balls) * 100 if balls > 0 else 0),
        'dismissal_rate': float((dismissals / balls) * 100 if balls > 0 else 0),
        'average': float(runs / dismissals if dismissals > 0 else runs)
    }

def get_top_batters(df, team, n=5):
    team_data = df[df['batting_team'] == team]
    stats = team_data.groupby('batter').agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()
    stats = stats[stats['ball'] >= 30].sort_values('runs_off_bat', ascending=False).head(n)
    return stats

# -----------------------------------------------------------------------------
# 3. Three.js 3D Visualization Helper
# -----------------------------------------------------------------------------

def render_threejs_chart(data, chart_type, title, width=600, height=400):
    div_id = f"chart_{uuid.uuid4().hex[:8]}"
    
    # Three.js Scripts for 3D visualizations
    scripts = {
        'grouped_bar_3d': f"""
            const margin = {{top: 50, right: 120, bottom: 50, left: 60}};
            const w = {width} - margin.left - margin.right;
            const h = {height} - margin.top - margin.bottom;
            const svg = d3.select("#{div_id}").append("svg").attr("width", {width}).attr("height", {height})
                .append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);
            
            // Tooltip
            const tooltip = d3.select("body").append("div")
                .attr("class", "d3-tooltip")
                .style("position", "absolute")
                .style("background", "white")
                .style("padding", "8px")
                .style("border", "1px solid #ccc")
                .style("border-radius", "4px")
                .style("opacity", 0)
                .style("pointer-events", "none");
            
            const x0 = d3.scaleBand().domain(data.map(d => d.category)).rangeRound([0, w]).paddingInner(0.1);
            const x1 = d3.scaleBand().domain(data[0].values.map(d => d.label)).rangeRound([0, x0.bandwidth()]).padding(0.05);
            const y = d3.scaleLinear().domain([0, d3.max(data, d => d3.max(d.values, v => v.value))]).nice().rangeRound([h, 0]);
            const color = d3.scaleOrdinal().range(["#FDB913", "#004BA0"]);
            
            const bars = svg.append("g").selectAll("g").data(data).join("g")
                .attr("transform", d => `translate(${{x0(d.category)}},0)`)
                .selectAll("rect").data(d => d.values).join("rect")
                .attr("x", d => x1(d.label))
                .attr("y", d => y(d.value))
                .attr("width", x1.bandwidth())
                .attr("height", d => h - y(d.value))
                .attr("fill", d => color(d.label))
                .attr("stroke", "#333")
                .attr("stroke-width", 0.5)
                .on("mouseover", function(event, d) {{
                    d3.select(this).attr("opacity", 0.7);
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`<strong>${{d.label}}</strong><br/>Run Rate: ${{d.value.toFixed(2)}}<br/>Balls: ${{d.balls || 'N/A'}}<br/>Wickets: ${{d.wickets || 'N/A'}}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                }})
                .on("mouseout", function() {{
                    d3.select(this).attr("opacity", 1);
                    tooltip.transition().duration(500).style("opacity", 0);
                }});
            
            // Value labels on bars
            svg.append("g").selectAll("g").data(data).join("g")
                .attr("transform", d => `translate(${{x0(d.category)}},0)`)
                .selectAll("text").data(d => d.values).join("text")
                .attr("x", d => x1(d.label) + x1.bandwidth()/2)
                .attr("y", d => y(d.value) - 5)
                .attr("text-anchor", "middle")
                .style("font-size", "10px")
                .style("fill", "#333")
                .text(d => d.value.toFixed(1));
                
            svg.append("g").attr("transform", `translate(0,${{h}})`).call(d3.axisBottom(x0))
                .selectAll("text").style("font-size", "11px");
            svg.append("g").call(d3.axisLeft(y).ticks(8))
                .selectAll("text").style("font-size", "11px");
            
            // Axis labels
            svg.append("text").attr("x", w/2).attr("y", h + 40)
                .attr("text-anchor", "middle").style("font-size", "12px").text("Match Phase");
            svg.append("text").attr("transform", "rotate(-90)")
                .attr("y", -45).attr("x", -h/2).attr("text-anchor", "middle")
                .style("font-size", "12px").text("Run Rate (runs per over)");
            
            // Legend
            const legend = svg.append("g").attr("font-family", "sans-serif").attr("font-size", 11)
                .attr("text-anchor", "start")
                .selectAll("g").data(data[0].values.map(d => d.label)).join("g")
                .attr("transform", (d, i) => `translate(${{w + 10}},${{i * 22}})`);
            legend.append("rect").attr("width", 18).attr("height", 18).attr("fill", color);
            legend.append("text").attr("x", 24).attr("y", 9).attr("dy", "0.35em").text(d => d);
        """,
        'bar': f"""
            const margin = {{top: 50, right: 30, bottom: 100, left: 60}};
            const w = {width} - margin.left - margin.right;
            const h = {height} - margin.top - margin.bottom;
            const svg = d3.select("#{div_id}").append("svg").attr("width", {width}).attr("height", {height})
                .append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);
            
            // Tooltip
            const tooltip = d3.select("body").append("div")
                .attr("class", "d3-tooltip")
                .style("position", "absolute")
                .style("background", "white")
                .style("padding", "8px")
                .style("border", "1px solid #ccc")
                .style("border-radius", "4px")
                .style("opacity", 0);
            
            const x = d3.scaleBand().domain(data.map(d => d.label)).range([0, w]).padding(0.2);
            const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value)]).nice().range([h, 0]);
            
            // Color gradient
            const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, d3.max(data, d => d.value)]);
            
            svg.append("g").selectAll("rect").data(data).join("rect")
                .attr("x", d => x(d.label))
                .attr("y", d => y(d.value))
                .attr("width", x.bandwidth())
                .attr("height", d => h - y(d.value))
                .attr("fill", d => colorScale(d.value))
                .attr("stroke", "#333")
                .attr("stroke-width", 0.5)
                .on("mouseover", function(event, d) {{
                    d3.select(this).attr("opacity", 0.7);
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`<strong>${{d.label}}</strong><br/>Strike Rate: ${{d.value.toFixed(2)}}<br/>Balls: ${{d.balls || 'N/A'}}<br/>Runs: ${{d.runs || 'N/A'}}<br/>Dismissals: ${{d.dismissals || 0}}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                }})
                .on("mouseout", function() {{
                    d3.select(this).attr("opacity", 1);
                    tooltip.transition().duration(500).style("opacity", 0);
                }});
            
            // Value labels
            svg.append("g").selectAll("text").data(data).join("text")
                .attr("x", d => x(d.label) + x.bandwidth()/2)
                .attr("y", d => y(d.value) - 5)
                .attr("text-anchor", "middle")
                .style("font-size", "10px")
                .style("fill", "#333")
                .text(d => d.value.toFixed(1));
            
            svg.append("g").attr("transform", `translate(0,${{h}})`).call(d3.axisBottom(x))
                .selectAll("text").attr("transform", "translate(-10,0)rotate(-45)")
                .style("text-anchor", "end").style("font-size", "10px");
            svg.append("g").call(d3.axisLeft(y).ticks(8))
                .selectAll("text").style("font-size", "11px");
            
            // Axis labels
            svg.append("text").attr("x", w/2).attr("y", h + 90)
                .attr("text-anchor", "middle").style("font-size", "12px").text("Player");
            svg.append("text").attr("transform", "rotate(-90)")
                .attr("y", -45).attr("x", -h/2).attr("text-anchor", "middle")
                .style("font-size", "12px").text("Strike Rate");
        """,
        'pie': f"""
            const width = {width};
            const height = {height};
            const radius = Math.min(width, height) / 2 - 50;
            const svg = d3.select("#{div_id}").append("svg").attr("width", width).attr("height", height)
                .append("g").attr("transform", `translate(${{width/2}},${{height/2}})`);
            
            // Tooltip
            const tooltip = d3.select("body").append("div")
                .attr("class", "d3-tooltip")
                .style("position", "absolute")
                .style("background", "white")
                .style("padding", "8px")
                .style("border", "1px solid #ccc")
                .style("border-radius", "4px")
                .style("opacity", 0);
            
            const color = d3.scaleOrdinal().domain(data.map(d => d.label)).range(d3.schemeSet3);
            const pie = d3.pie().value(d => d.value).sort(null);
            const data_ready = pie(data);
            const arc = d3.arc().innerRadius(radius * 0.5).outerRadius(radius);
            
            // Calculate total
            const total = data.reduce((sum, d) => sum + d.value, 0);
            
            svg.selectAll('path').data(data_ready).join('path')
                .attr('d', arc)
                .attr('fill', d => color(d.data.label))
                .attr("stroke", "white")
                .style("stroke-width", "2px")
                .style("opacity", 0.8)
                .on("mouseover", function(event, d) {{
                    d3.select(this).style("opacity", 1).attr("stroke-width", "3px");
                    const percentage = ((d.data.value / total) * 100).toFixed(1);
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`<strong>${{d.data.label}} runs</strong><br/>Count: ${{d.data.value}}<br/>Percentage: ${{percentage}}%`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                }})
                .on("mouseout", function() {{
                    d3.select(this).style("opacity", 0.8).attr("stroke-width", "2px");
                    tooltip.transition().duration(500).style("opacity", 0);
                }});
            
            // Labels with percentages
            const outerArc = d3.arc().innerRadius(radius * 1.1).outerRadius(radius * 1.1);
            svg.selectAll('polyline').data(data_ready).join('polyline')
                .attr("stroke", "#333")
                .style("fill", "none")
                .attr("stroke-width", 1)
                .attr('points', d => {{
                    const posA = arc.centroid(d);
                    const posB = outerArc.centroid(d);
                    const posC = outerArc.centroid(d);
                    const midangle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                    posC[0] = radius * 0.95 * (midangle < Math.PI ? 1 : -1);
                    return [posA, posB, posC];
                }});
            
            svg.selectAll('text').data(data_ready).join('text')
                .text(d => {{
                    const percentage = ((d.data.value / total) * 100).toFixed(1);
                    return `${{d.data.label}} (${{percentage}}%)`;
                }})
                .attr('transform', d => {{
                    const pos = outerArc.centroid(d);
                    const midangle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                    pos[0] = radius * 1.0 * (midangle < Math.PI ? 1 : -1);
                    return `translate(${{pos}})`;
                }})
                .style('text-anchor', d => {{
                    const midangle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                    return midangle < Math.PI ? "start" : "end";
                }})
                .style('font-size', 11)
                .style('fill', '#333');
            
            // Center text with total
            svg.append("text").attr("text-anchor", "middle").attr("dy", "-0.2em")
                .style("font-size", "18px").style("font-weight", "bold").text("Total");
            svg.append("text").attr("text-anchor", "middle").attr("dy", "1.2em")
                .style("font-size", "16px").text(total);
        """
    }

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><script src="https://d3js.org/d3.v7.min.js"></script></head>
    <body>
        <h3 style="font-family: sans-serif; text-align: center;">{title}</h3>
        <div id="{div_id}"></div>
        <script>
            const data = {json.dumps(data)};
            {scripts[chart_type]}
        </script>
    </body>
    </html>
    """
    return html

# -----------------------------------------------------------------------------
# 4. Main Application
# -----------------------------------------------------------------------------

st.title("🏏 IPL Team Performance Analysis")
st.markdown("Interactive dashboard using **Streamlit** and **D3.js**")

with st.spinner("Loading Data..."):
    df = load_data()

# Sidebar Controls
st.sidebar.header("Analysis Settings")
teams = sorted(df['batting_team'].unique())
team1 = st.sidebar.selectbox("Select Team 1", teams, index=0)
team2 = st.sidebar.selectbox("Select Team 2", teams, index=1 if len(teams) > 1 else 0)

bowler_types = ['Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
bowler_type = st.sidebar.selectbox("Select Bowler Type", bowler_types)

# Layout
col1, col2 = st.columns(2)

# 1. Phase Analysis
st.subheader(f"📊 Phase Analysis: {team1} vs {team2}")
t1_stats = calculate_run_rate_by_phase(df, team1)
t2_stats = calculate_run_rate_by_phase(df, team2)
phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
phase_data = []
for phase in phases:
    t1_phase = t1_stats[t1_stats['phase'] == phase]
    t2_phase = t2_stats[t2_stats['phase'] == phase]
    
    val1 = float(t1_phase['run_rate'].values[0]) if not t1_phase.empty else 0.0
    val2 = float(t2_phase['run_rate'].values[0]) if not t2_phase.empty else 0.0
    balls1 = int(t1_phase['ball'].values[0]) if not t1_phase.empty else 0
    balls2 = int(t2_phase['ball'].values[0]) if not t2_phase.empty else 0
    wickets1 = int(t1_phase['wickets'].values[0]) if not t1_phase.empty else 0
    wickets2 = int(t2_phase['wickets'].values[0]) if not t2_phase.empty else 0
    
    phase_data.append({
        'category': str(phase),
        'values': [
            {'label': str(team1), 'value': val1, 'balls': balls1, 'wickets': wickets1},
            {'label': str(team2), 'value': val2, 'balls': balls2, 'wickets': wickets2}
        ]
    })

# Display summary statistics
col_a, col_b = st.columns(2)
with col_a:
    st.metric(f"{team1} Overall Run Rate", f"{t1_stats['run_rate'].mean():.2f}")
with col_b:
    st.metric(f"{team2} Overall Run Rate", f"{t2_stats['run_rate'].mean():.2f}")

components.html(render_d3_chart(phase_data, 'grouped_bar', "Run Rate Comparison by Phase", 900, 450), height=500)

# 2. Matchup Analysis
st.subheader(f"🎯 Player Matchups vs {bowler_type}")
c1, c2 = st.columns(2)

with c1:
    st.markdown(f"**{team1} Top Batters**")
    batters1_df = get_top_batters(df, team1, n=5)
    if not batters1_df.empty:
        batters1 = batters1_df['batter'].tolist()
        m1_data = []
        for b in batters1:
            s = calculate_player_matchup(df, b, bowler_type)
            if s: 
                m1_data.append({
                    'label': str(b), 
                    'value': float(s['strike_rate']),
                    'balls': int(s['balls_faced']),
                    'runs': int(s['runs_scored']),
                    'dismissals': int(s['dismissals'])
                })
        
        if m1_data:
            components.html(render_d3_chart(m1_data, 'bar', f"{team1} vs {bowler_type}", 450, 350), height=400)
            # Display data table
            st.dataframe(pd.DataFrame(m1_data)[['label', 'runs', 'balls', 'value']].rename(
                columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}
            ), hide_index=True)
        else:
            st.info(f"No data for {team1} vs {bowler_type}")
    else:
        st.warning(f"No batters found for {team1}")

with c2:
    st.markdown(f"**{team2} Top Batters**")
    batters2_df = get_top_batters(df, team2, n=5)
    if not batters2_df.empty:
        batters2 = batters2_df['batter'].tolist()
        m2_data = []
        for b in batters2:
            s = calculate_player_matchup(df, b, bowler_type)
            if s: 
                m2_data.append({
                    'label': str(b), 
                    'value': float(s['strike_rate']),
                    'balls': int(s['balls_faced']),
                    'runs': int(s['runs_scored']),
                    'dismissals': int(s['dismissals'])
                })
        
        if m2_data:
            components.html(render_d3_chart(m2_data, 'bar', f"{team2} vs {bowler_type}", 450, 350), height=400)
            # Display data table
            st.dataframe(pd.DataFrame(m2_data)[['label', 'runs', 'balls', 'value']].rename(
                columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}
            ), hide_index=True)
        else:
            st.info(f"No data for {team2} vs {bowler_type}")
    else:
        st.warning(f"No batters found for {team2}")

# 3. Runs Distribution
st.subheader("📈 Runs Distribution")
d1, d2 = st.columns(2)

with d1:
    rd1 = df[df['batting_team'] == team1]['runs_off_bat'].value_counts().sort_index()
    pie1_data = [{'label': str(k), 'value': int(v)} for k, v in rd1.items()]
    components.html(render_d3_chart(pie1_data, 'pie', f"{team1} Runs", 400, 300), height=350)

with d2:
    rd2 = df[df['batting_team'] == team2]['runs_off_bat'].value_counts().sort_index()
    pie2_data = [{'label': str(k), 'value': int(v)} for k, v in rd2.items()]
    components.html(render_d3_chart(pie2_data, 'pie', f"{team2} Runs", 400, 300), height=350)
