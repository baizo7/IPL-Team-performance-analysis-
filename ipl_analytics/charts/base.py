"""
Base Plotly Layout Themes & Color Utilities
"""

from typing import Dict, Any
import plotly.graph_objects as go
from ipl_analytics.utils.theme import IPL_TEAM_COLORS


def get_plotly_layout_theme(title: str, height: int = 420) -> Dict[str, Any]:
    """Return standard dark theme layout parameters for Plotly figures."""
    return dict(
        title=f"<b>{title}</b>",
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#e2e8f0', family='Inter, sans-serif'),
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=False, tickfont=dict(color='#cbd5e1')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8'))
    )


def get_team_color(team_name: str) -> str:
    """Resolve team color HEX code from IPL_TEAM_COLORS mapping."""
    return IPL_TEAM_COLORS.get(team_name, '#38bdf8')
