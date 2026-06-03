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
        df = pd.read_csv(csv_file, low_memory=False)
    else:
        # Logic to load from folder or create sample
        if not os.path.exists(path):
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
    elif 'over' in df.columns:
        df['over'] = pd.to_numeric(df['over'], errors='coerce').fillna(1).astype(int)
    else:
        df['over'] = 1
        
    # Runs
    if 'runs_off_bat' in df.columns and 'extras' in df.columns:
        df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
        df['extras'] = pd.to_numeric(df['extras'], errors='coerce').fillna(0)
        df['total_runs'] = df['runs_off_bat'] + df['extras']
    elif 'runs_off_bat' in df.columns:
        df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
        df['total_runs'] = df['runs_off_bat']
    else:
        df['total_runs'] = 0
        
    # Phase
    df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21], labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)'])
    
    # Wickets
    if 'wicket_type' in df.columns:
        df['is_wicket'] = df['wicket_type'].notna().astype(int)
    else:
        df['is_wicket'] = 0
        
    # Bowler types
    if 'bowler' in df.columns:
        def get_bowler_type(bowler_name):
            if pd.isna(bowler_name): return 'Unknown'
            name = str(bowler_name).lower()
            
            left_arm_pacers = ['boult', 'arshdeep', 'natarajan', 'mustafizur', 'curran', 'starc']
            left_arm_wrist = ['kuldeep yadav', 'noor ahmad', 'tabraiz shamsi']
            left_arm_orthodox = ['jadeja', 'axar', 'krunal', 'shahbaz', 'santner']
            right_arm_leg = ['rashid', 'chahal', 'bishnoi', 'hasaranga', 'zampa']
            right_arm_off = ['ashwin', 'narine', 'chakravarthy', 'theekshana', 'livingstone']
            
            if any(p in name for p in left_arm_pacers):
                return 'Left-Arm Pace'
            elif any(p in name for p in left_arm_wrist):
                return 'Left-Arm Wrist Spin'
            elif any(p in name for p in left_arm_orthodox):
                return 'Left-Arm Orthodox'
            elif any(p in name for p in right_arm_leg):
                return 'Right-Arm Leg Spin'
            elif any(p in name for p in right_arm_off):
                return 'Right-Arm Off Spin'
            else:
                return 'Right-Arm Pace'

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
    data_json = json.dumps(data)
    
    if chart_type == 'grouped_bar_3d':
        script = f"""
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f5f5);
        
        const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
        camera.position.set(15, 15, 15);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize({width}, {height});
        document.getElementById('{div_id}').appendChild(renderer.domElement);
        
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        scene.add(directionalLight);
        
        let maxValue = 0;
        data.forEach(cat => {{
            cat.values.forEach(val => {{
                if (val.value > maxValue) maxValue = val.value;
            }});
        }});
        
        const barWidth = 1.5;
        const barDepth = 1.5;
        const spacing = 5;
        const groupSpacing = 2;
        const colors = [0xFDB913, 0x004BA0];
        
        data.forEach((category, catIndex) => {{
            category.values.forEach((val, teamIndex) => {{
                const height = (val.value / maxValue) * 10;
                const geometry = new THREE.BoxGeometry(barWidth, height, barDepth);
                const material = new THREE.MeshPhongMaterial({{ color: colors[teamIndex], shininess: 100 }});
                const bar = new THREE.Mesh(geometry, material);
                
                const xPos = catIndex * spacing - (data.length * spacing / 2);
                const zPos = teamIndex * groupSpacing - 1;
                bar.position.set(xPos, height/2, zPos);
                
                bar.userData = {{
                    team: val.label,
                    phase: category.category,
                    value: val.value.toFixed(2),
                    balls: val.balls || 0,
                    wickets: val.wickets || 0
                }};
                
                scene.add(bar);
            }});
        }});
        
        const gridHelper = new THREE.GridHelper(30, 30, 0x888888, 0xdddddd);
        scene.add(gridHelper);
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        """
    
    elif chart_type == 'bar_3d':
        script = f"""
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f5f5);
        
        const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
        camera.position.set(10, 10, 15);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize({width}, {height});
        document.getElementById('{div_id}').appendChild(renderer.domElement);
        
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        scene.add(directionalLight);
        
        const maxValue = Math.max(...data.map(d => d.value));
        const barWidth = 1.5;
        const spacing = 3;
        
        data.forEach((item, index) => {{
            const height = (item.value / maxValue) * 10;
            const hue = (index / data.length) * 0.7;
            
            const geometry = new THREE.BoxGeometry(barWidth, height, barWidth);
            const material = new THREE.MeshPhongMaterial({{ 
                color: new THREE.Color().setHSL(hue, 0.7, 0.5),
                shininess: 100
            }});
            const bar = new THREE.Mesh(geometry, material);
            
            bar.position.set((index - data.length/2) * spacing, height/2, 0);
            bar.userData = {{
                player: item.label,
                strikeRate: item.value.toFixed(2),
                balls: item.balls || 0,
                runs: item.runs || 0,
                dismissals: item.dismissals || 0
            }};
            
            scene.add(bar);
        }});
        
        const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xdddddd);
        scene.add(gridHelper);
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        """
    
    elif chart_type == 'pie_3d':
        script = f"""
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f5f5);
        
        const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
        camera.position.set(0, 8, 12);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize({width}, {height});
        document.getElementById('{div_id}').appendChild(renderer.domElement);
        
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        scene.add(directionalLight);
        
        const total = data.reduce((sum, item) => sum + item.value, 0);
        let currentAngle = 0;
        const innerRadius = 2;
        const outerRadius = 5;
        const depth = 1;
        
        data.forEach((item, index) => {{
            const angle = (item.value / total) * Math.PI * 2;
            const hue = (index / data.length);
            
            const shape = new THREE.Shape();
            const startAngle = currentAngle;
            const endAngle = currentAngle + angle;
            
            shape.moveTo(outerRadius * Math.cos(startAngle), outerRadius * Math.sin(startAngle));
            shape.absarc(0, 0, outerRadius, startAngle, endAngle, false);
            shape.lineTo(innerRadius * Math.cos(endAngle), innerRadius * Math.sin(endAngle));
            shape.absarc(0, 0, innerRadius, endAngle, startAngle, true);
            
            const geometry = new THREE.ExtrudeGeometry(shape, {{
                depth: depth,
                bevelEnabled: true,
                bevelThickness: 0.1,
                bevelSize: 0.1,
                bevelSegments: 2
            }});
            
            const material = new THREE.MeshPhongMaterial({{ 
                color: new THREE.Color().setHSL(hue, 0.8, 0.6),
                shininess: 100
            }});
            
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.z = -depth/2;
            mesh.userData = {{
                label: item.label,
                value: item.value,
                percentage: ((item.value / total) * 100).toFixed(1)
            }};
            
            scene.add(mesh);
            currentAngle = endAngle;
        }});
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        """
    else:
        script = ""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; padding: 20px; font-family: sans-serif; }}
            #title {{ text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
            #{div_id} {{ border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        </style>
    </head>
    <body>
        <div id="title">{title}</div>
        <div id="{div_id}"></div>
        <script>
            const data = {data_json};
            {script}
        </script>
    </body>
    </html>
    """
    return html

# -----------------------------------------------------------------------------
# 4. Main Application
# -----------------------------------------------------------------------------

st.title("🏏 IPL Team Performance Analysis")
st.markdown("Interactive dashboard using **Streamlit** and **Three.js** 3D visualizations")

with st.spinner("Loading Data..."):
    df = load_data()

# Sidebar Controls
st.sidebar.header("Analysis Settings")
teams = sorted(df['batting_team'].unique())
team1 = st.sidebar.selectbox("Select Team 1", teams, index=0)
team2 = st.sidebar.selectbox("Select Team 2", teams, index=1 if len(teams) > 1 else 0)

bowler_types = ['Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
bowler_type = st.sidebar.selectbox("Select Bowler Type", bowler_types)

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

col_a, col_b = st.columns(2)
with col_a:
    st.metric(f"{team1} Overall Run Rate", f"{t1_stats['run_rate'].mean():.2f}")
with col_b:
    st.metric(f"{team2} Overall Run Rate", f"{t2_stats['run_rate'].mean():.2f}")

components.html(render_threejs_chart(phase_data, 'grouped_bar_3d', "3D Run Rate Comparison by Phase", 900, 500), height=550)

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
            components.html(render_threejs_chart(m1_data, 'bar_3d', f"{team1} vs {bowler_type}", 450, 400), height=450)
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
            components.html(render_threejs_chart(m2_data, 'bar_3d', f"{team2} vs {bowler_type}", 450, 400), height=450)
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
    components.html(render_threejs_chart(pie1_data, 'pie_3d', f"{team1} Runs", 450, 400), height=450)

with d2:
    rd2 = df[df['batting_team'] == team2]['runs_off_bat'].value_counts().sort_index()
    pie2_data = [{'label': str(k), 'value': int(v)} for k, v in rd2.items()]
    components.html(render_threejs_chart(pie2_data, 'pie_3d', f"{team2} Runs", 450, 400), height=450)
