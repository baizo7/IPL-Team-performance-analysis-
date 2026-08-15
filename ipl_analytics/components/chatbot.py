import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import os


def render_chatbot(api_key: str = "", df=None, team1: str = "Chennai Super Kings", team2: str = "Delhi Capitals") -> None:
    """Render the floating AI analyst chatbot using external HTML/JS files."""
    
    default_key = (
        api_key
        or st.session_state.get("gemini_api_key", "")
        or os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    )

    t1_name = team1 or "Team 1"
    t2_name = team2 or "Team 2"

    t1_runs, t1_balls, t1_rr, t1_fours, t1_sixes, t1_wickets, t1_dot_pct = 0, 0, 0.0, 0, 0, 0, 0.0
    t1_top_name, t1_top_runs = "N/A", 0

    t2_runs, t2_balls, t2_rr, t2_fours, t2_sixes, t2_wickets, t2_dot_pct = 0, 0, 0.0, 0, 0, 0, 0.0
    t2_top_name, t2_top_runs = "N/A", 0

    if df is not None and not df.empty:
        try:
            batter_col = 'batter' if 'batter' in df.columns else ('striker' if 'striker' in df.columns else 'batsman')
            runs_bat_col = 'runs_off_bat' if 'runs_off_bat' in df.columns else ('batsman_runs' if 'batsman_runs' in df.columns else 'runs_of_bat')

            def _get_team_sub_df(tdf, team_name):
                aliases = [team_name]
                if team_name == 'Delhi Capitals':
                    aliases.append('Delhi Daredevils')
                elif 'RCB' in team_name or 'Bangalore' in team_name or 'Bengaluru' in team_name:
                    aliases.extend(['Royal Challengers Bangalore', 'Royal Challengers Bengaluru'])
                elif 'Punjab' in team_name:
                    aliases.extend(['Punjab Kings', 'Kings XI Punjab'])
                elif 'Sunrisers' in team_name or 'Hyderabad' in team_name:
                    aliases.extend(['Sunrisers Hyderabad', 'Deccan Chargers'])
                return tdf[tdf['batting_team'].isin(aliases)]

            df1 = _get_team_sub_df(df, t1_name)
            if not df1.empty:
                t1_balls = len(df1)
                t1_runs = int(df1['total_runs'].sum()) if 'total_runs' in df1.columns else int(df1[runs_bat_col].sum())
                t1_rr = round((t1_runs / t1_balls) * 6, 2) if t1_balls > 0 else 0.0

                if 'is_four' in df1.columns:
                    t1_fours = int(df1['is_four'].sum())
                else:
                    t1_fours = int((df1[runs_bat_col] == 4).sum())

                if 'is_six' in df1.columns:
                    t1_sixes = int(df1['is_six'].sum())
                else:
                    t1_sixes = int((df1[runs_bat_col] == 6).sum())

                t1_wickets = int(df1['is_wicket'].sum()) if 'is_wicket' in df1.columns else 0
                dots1 = int((df1[runs_bat_col] == 0).sum())
                t1_dot_pct = round((dots1 / t1_balls) * 100, 1) if t1_balls > 0 else 0.0

                if batter_col in df1.columns and runs_bat_col in df1.columns:
                    top1 = df1.groupby(batter_col)[runs_bat_col].sum().sort_values(ascending=False)
                    if not top1.empty:
                        t1_top_name = str(top1.index[0])
                        t1_top_runs = int(top1.iloc[0])

            df2 = _get_team_sub_df(df, t2_name)
            if not df2.empty:
                t2_balls = len(df2)
                t2_runs = int(df2['total_runs'].sum()) if 'total_runs' in df2.columns else int(df2[runs_bat_col].sum())
                t2_rr = round((t2_runs / t2_balls) * 6, 2) if t2_balls > 0 else 0.0

                if 'is_four' in df2.columns:
                    t2_fours = int(df2['is_four'].sum())
                else:
                    t2_fours = int((df2[runs_bat_col] == 4).sum())

                if 'is_six' in df2.columns:
                    t2_sixes = int(df2['is_six'].sum())
                else:
                    t2_sixes = int((df2[runs_bat_col] == 6).sum())

                t2_wickets = int(df2['is_wicket'].sum()) if 'is_wicket' in df2.columns else 0
                dots2 = int((df2[runs_bat_col] == 0).sum())
                t2_dot_pct = round((dots2 / t2_balls) * 100, 1) if t2_balls > 0 else 0.0

                if batter_col in df2.columns and runs_bat_col in df2.columns:
                    top2 = df2.groupby(batter_col)[runs_bat_col].sum().sort_values(ascending=False)
                    if not top2.empty:
                        t2_top_name = str(top2.index[0])
                        t2_top_runs = int(top2.iloc[0])
        except Exception:
            pass

    # Read HTML template and inject runtime values
    html_path = Path(__file__).parent.parent / "static" / "chatbot.html"
    html_template = html_path.read_text(encoding="utf-8")

    html_content = html_template.replace("{{DEFAULT_KEY}}", default_key) \
        .replace("{{TEAM1}}", t1_name) \
        .replace("{{TEAM2}}", t2_name) \
        .replace("{{T1_RUNS}}", str(t1_runs)) \
        .replace("{{T1_BALLS}}", str(t1_balls)) \
        .replace("{{T1_RR}}", str(t1_rr)) \
        .replace("{{T1_FOURS}}", str(t1_fours)) \
        .replace("{{T1_SIXES}}", str(t1_sixes)) \
        .replace("{{T1_WICKETS}}", str(t1_wickets)) \
        .replace("{{T1_DOT_PCT}}", str(t1_dot_pct)) \
        .replace("{{T1_TOP_NAME}}", t1_top_name) \
        .replace("{{T1_TOP_RUNS}}", str(t1_top_runs)) \
        .replace("{{T2_RUNS}}", str(t2_runs)) \
        .replace("{{T2_BALLS}}", str(t2_balls)) \
        .replace("{{T2_RR}}", str(t2_rr)) \
        .replace("{{T2_FOURS}}", str(t2_fours)) \
        .replace("{{T2_SIXES}}", str(t2_sixes)) \
        .replace("{{T2_WICKETS}}", str(t2_wickets)) \
        .replace("{{T2_DOT_PCT}}", str(t2_dot_pct)) \
        .replace("{{T2_TOP_NAME}}", t2_top_name) \
        .replace("{{T2_TOP_RUNS}}", str(t2_top_runs))

    st.markdown("""
    <style>
    iframe[srcdoc*="IPL AI Analyst"] {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        width: 70px !important;
        height: 70px !important;
        z-index: 9999999 !important;
        border: none !important;
        background: transparent !important;
        transition: width 0.3s ease, height 0.3s ease !important;
    }
    </style>
    """, unsafe_allow_html=True)

    components.html(html_content, height=580, width=380)