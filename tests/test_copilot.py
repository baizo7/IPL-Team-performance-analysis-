"""
Unit tests for AI Copilot intent parser and analytics tools.
"""

import pandas as pd
from ipl_analytics.services.ai_copilot import process_copilot_command


def test_copilot_player_comparison_intent():
    df = pd.DataFrame([
        {'batter': 'Shubman Gill', 'runs_off_bat': 4, 'is_wicket': 0, 'is_four': 1, 'is_six': 0},
        {'batter': 'RD Gaikwad', 'runs_off_bat': 6, 'is_wicket': 0, 'is_four': 0, 'is_six': 1},
    ])
    report, nav = process_copilot_command("Compare Shubman Gill vs RD Gaikwad", df)
    assert "Shubman Gill" in report
    assert "RD Gaikwad" in report
    assert nav["target_section"] == "👤 Player Stats"


def test_copilot_navigation_intent():
    df = pd.DataFrame()
    report, nav = process_copilot_command("open 3d pitch map", df)
    assert nav["target_section"] == "🎯 Pitch Maps & Wagon Wheel"
