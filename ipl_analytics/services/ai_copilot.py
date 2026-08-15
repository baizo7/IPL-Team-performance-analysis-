"""
AI Copilot Service
Intent parser, natural language analytics dispatcher, and side-by-side player comparisons.
"""

from typing import Tuple, Dict, Any
import ipl_copilot


def process_copilot_command(user_query: str, df: Any) -> Tuple[str, Dict[str, Any]]:
    """Parse user command, execute pandas analytics tool call, return report & navigation state."""
    return ipl_copilot.process_copilot_command(user_query, df)
