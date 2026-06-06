# 🏏 IPL Team Performance Analysis Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75)
![Three.js](https://img.shields.io/badge/Three.js-3D_Visuals-black)

A highly interactive, deeply analytical, and visually stunning web application built with Streamlit to analyze Indian Premier League (IPL) ball-by-ball data from 2008 to the present day.


Experience this on----> https://67jbqtnspdombpagauxc2r.streamlit.app/

## ✨ Features

*   **Secure Authenticated Access:** Clean, secure login panel protecting your analytics dashboard.
*   **Deep Team Matchups:** Select any two IPL franchises and directly compare their performance across different match phases (Powerplay, Middle Overs, Death Overs).
*   **3D Interactive Pitch Maps & Wagon Wheels:** Next-generation 3D visualizations rendered directly in the browser. Rotate, zoom, and inspect ball trajectories, bowling lengths, and shot directions in a 3D stadium environment.
*   **Advanced Statistical Visualizations:**
    *   **Phase Analysis:** Dynamic run-rate comparisons between teams.
    *   **Runs Distribution:** Monochromatic, team-branded donut and bar charts showing boundary vs. rotation of strike metrics.
    *   **Bowler Economy Profiles:** Gradient and team-colored horizontal bar charts showcasing top bowler performances.
    *   **Strike Rate Progression:** Top 15 batters compared using official franchise colors.
*   **Dynamic Theming:** Built-in dark mode aesthetic with custom CSS. All charts intelligently adapt to the official hex colors of the selected IPL franchises.

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.8+ installed. 

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/baizo7/IPL-Team-performance-analysis-.git
   cd IPL-Team-performance-analysis-
   ```
2. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
Launch the Streamlit dashboard locally:
```bash
streamlit run app.py
```
*(The dashboard runs on `http://localhost:8501` by default)*

## 📂 Project Structure
*   `app.py` / `legacy_app.py`: The core Streamlit application scripts housing the UI and logic.
*   `ipl_data/` & `data/`: Contains the ball-by-ball CSV datasets used for generating the statistics.
*   `pages/`: Contains the `1_Login.py` authentication UI.
*   `static/` & `assets/`: 3D models (like `stadium.glb`) and static HTML/JS wrappers for Three.js components.

## 🛠️ Built With
*   **[Streamlit](https://streamlit.io/)** - The web framework used.
*   **[Pandas](https://pandas.pydata.org/)** - For heavy data manipulation and ball-by-ball metric aggregations.
*   **[Plotly](https://plotly.com/python/) & [Altair](https://altair-viz.github.io/)** - For dynamic, interactive 2D charts.
*   **[Three.js](https://threejs.org/)** - For generating 3D Pitch Maps and Wagon Wheels.

## 📝 License
This project is open-source and available for educational and analytical purposes.
