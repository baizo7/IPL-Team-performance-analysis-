# 🎯 Pitch Maps Feature - IPL Performance Analysis

## Overview
Added interactive 3D pitch map visualizations to show ball landing positions and outcomes on the cricket pitch.

## What Are Pitch Maps?
Pitch maps display where balls landed on the cricket pitch (22 yards) with:
- **X-axis**: Width (-1.2 to 1.2) - Left to right from bowler's perspective
- **Y-axis**: Length (0 to 22 yards) - Bowler's end to batter's end
- **Color coding**: Different colors for different outcomes
- **Size**: Larger markers for more significant outcomes

## Color Coding System

| Color | Outcome | Description |
|-------|---------|-------------|
| 🔴 Red | Wicket | Dismissal of batter |
| 🟣 Purple | Six (6 runs) | Ball cleared boundary |
| 🟢 Green | Four (4 runs) | Ball reached boundary |
| 🔵 Blue | 1-3 runs | Singles, doubles, triples |
| ⚫ Gray | Dot ball (0) | No runs scored |

## Ball Position Logic

### Good Length (6-10 yards from bowler)
- Most wickets occur here
- Typically on or around off-stump (x ≈ 0.3)
- Forces batters to make decisions

### Short Pitched (0-6 yards)
- Often pulled or hooked for sixes
- Can be uncomfortable for batters
- Risk of wickets if mistimed

### Full Length (10-16 yards)
- Can be driven for fours
- Good for scoring runs
- Risky if too full (becomes half-volley)

### Very Full/Yorkers (16-22 yards)
- Landing near batter's feet
- Hard to score off
- Can produce sixes if slightly off
- Effective for death overs

## Features

### 1. Interactive 3D Visualization
- **Rotate**: Click and drag to view from any angle
- **Zoom**: Scroll to zoom in/out
- **Pan**: Right-click and drag to pan
- **Hover**: Hover over balls to see details

### 2. Pitch Elements
- **Green Surface**: Cricket pitch (22 yards)
- **Brown Stumps**: Three stumps at each end
- **White Creases**: Bowling and batting creases
- **Grid**: Ground reference for depth perception

### 3. Filters Available
- **Team**: View specific team's batting
- **Bowler Type**: Filter by bowler type (pace/spin)
- **Phase**: Powerplay, Middle overs, Death overs
- **All Phases**: Combined view

### 4. Data Insights

#### Wicket Clusters
- Red balls show where dismissals occur
- Typically concentrated in good length area
- Line analysis shows preferred dismissal zones

#### Boundary Patterns
- Green (4s) and Purple (6s) show scoring areas
- Short balls often → sixes
- Full balls often → fours
- Width analysis shows preferred hitting zones

#### Dot Ball Analysis
- Gray balls show where runs were restricted
- Helps identify effective bowling lengths
- Shows defensive batting patterns

## How to Use

### Jupyter Notebook
```python
# Generate pitch map for a team
pitch_map = create_pitch_map(
    df, 
    team="Chennai Super Kings",
    phase="Powerplay (1-6)",
    bowler_type="Right-Arm Pace"
)
display(pitch_map)
```

### Streamlit App
1. Open http://localhost:8501
2. Select teams from sidebar
3. Choose bowler type and phase
4. Scroll to "Pitch Maps" section
5. Interact with 3D visualizations

## Technical Implementation

### Data Generation
- Samples up to 500 balls per visualization (performance)
- Simulates pitch positions based on outcomes
- Uses normal distributions for realistic spread
- Accounts for different ball types

### 3D Rendering
- **Engine**: Three.js (WebGL)
- **Controls**: OrbitControls for camera
- **Lighting**: Ambient + Directional lights
- **Materials**: Phong materials for realistic appearance
- **Geometry**: Spheres for balls, planes for pitch

### Position Simulation
Since Cricsheet data doesn't include exact ball landing positions, we simulate based on:
- **Outcome**: Runs scored or wicket taken
- **Statistical distributions**: Real cricket patterns
- **Length variations**: Based on delivery type
- **Line variations**: Based on outcome success

## Performance Considerations

1. **Data Sampling**: Limited to 500 balls per visualization
2. **Random Seed**: Consistent visualizations (seed=42)
3. **WebGL Rendering**: Hardware-accelerated graphics
4. **Efficient Geometry**: Low-poly models for smooth performance

## Future Enhancements

### Potential Additions
1. **Real Position Data**: If available from ball-tracking systems
2. **Heat Maps**: Density overlays for common landing zones
3. **Trajectory Arcs**: 3D ball paths from bowler to pitch
4. **Wagon Wheels**: Shot direction overlays
5. **Comparison Views**: Side-by-side team comparisons
6. **Animation**: Time-based replay of deliveries
7. **Statistical Overlays**: Zone-based statistics

### Advanced Analytics
1. **Length Analysis**: Distribution charts by length
2. **Line Analysis**: Off/leg side percentages
3. **Success Rates**: Outcomes by pitch location
4. **Bowler Patterns**: Individual bowler tendencies
5. **Batter Preferences**: Scoring zone analysis

## Example Use Cases

### 1. Team Strategy Analysis
- Identify where opposition scores most runs
- Find wicket-taking lengths/lines
- Analyze powerplay vs death overs tactics

### 2. Bowler Performance
- View individual bowler pitch maps
- Compare fast vs spin bowlers
- Analyze economy rate patterns

### 3. Batter Weaknesses
- Identify dismissal zones
- Find scoring gaps
- Analyze phase-wise tendencies

### 4. Match Planning
- Study venue-specific patterns
- Prepare field placements
- Plan bowling strategies

## Code Structure

### Notebook (`ipl_perfromance_analysis.ipynb`)
- Cell 8: `generate_pitch_map_data()` function
- Cell 10: `create_pitch_map()` function
- Cell 13: Dashboard with pitch map integration

### Streamlit App (`app.py`)
- Line ~196: `generate_pitch_map_data()` function
- Line ~498: `render_pitch_map()` function
- Line ~693: Pitch Maps UI section

## Dependencies
- **Three.js r128**: 3D graphics engine
- **OrbitControls**: Camera controls
- **pandas/numpy**: Data processing
- **Streamlit**: Web app framework
- **IPython**: Notebook HTML display

## Credits
- **Data Source**: Cricsheet.org (Ball-by-ball IPL data)
- **Visualization**: Three.js WebGL library
- **Position Simulation**: Statistical modeling based on cricket physics

---

**Note**: Pitch positions are simulated based on statistical patterns since Cricsheet data doesn't include exact ball landing coordinates. Real ball-tracking data would provide more accurate visualizations.
