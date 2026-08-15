"""
IPL Copilot - Autonomous Analytics & Navigation Engine
Modular tool registry executing Pandas analytics, Hawk-Eye telemetry lookups,
and triggering Streamlit dashboard state updates.
"""

import re
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any


class AnalyticsToolRegistry:
    """Registry of executable analytics tools."""

    @staticmethod
    def _find_player(df, name_query: str) -> str:
        """Ranked fuzzy player finder in dataset by name query."""
        if df is None or df.empty or not name_query:
            return name_query

        batter_col = 'batter' if 'batter' in df.columns else ('striker' if 'striker' in df.columns else 'batsman')
        bowler_col = 'bowler' if 'bowler' in df.columns else 'bowler'

        all_players = set()
        if batter_col in df.columns:
            all_players.update(df[batter_col].dropna().unique())
        if bowler_col in df.columns:
            all_players.update(df[bowler_col].dropna().unique())

        clean_query = str(name_query).strip().lower()
        query_parts = clean_query.split()

        # 1. Rank 1: Exact case-insensitive match
        for p in all_players:
            if str(p).strip().lower() == clean_query:
                return str(p)

        # 2. Rank 2: Initial + Surname match (e.g. 'suryakumar yadav' -> 'SA Yadav' or 'S Yadav')
        if len(query_parts) >= 2:
            q_init = query_parts[0][0]
            q_surname = query_parts[-1]
            for p in all_players:
                p_str = str(p).lower()
                if q_surname in p_str and (q_init in p_str or p_str.startswith(q_init)):
                    return str(p)

        # 3. Rank 3: All query tokens present in player name
        for p in all_players:
            p_str = str(p).lower()
            if all(part in p_str for part in query_parts):
                return str(p)

        # 4. Rank 4: Surname match
        last_part = query_parts[-1] if query_parts else ''
        if len(last_part) > 2:
            matches = [str(p) for p in all_players if last_part in str(p).lower()]
            if matches:
                # Prefer match starting with first initial if available
                first_init = query_parts[0][0] if query_parts else ''
                for m in matches:
                    if m.lower().startswith(first_init):
                        return m
                return matches[0]

        return name_query

    @classmethod
    def compare_players(cls, player1: str, player2: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Side-by-side Pandas analytical comparison of two players."""
        if df is None or df.empty:
            return "⚠️ No dataset loaded for player comparison.", {}

        p1_name = cls._find_player(df, player1)
        p2_name = cls._find_player(df, player2)

        batter_col = 'batter' if 'batter' in df.columns else ('striker' if 'striker' in df.columns else 'batsman')
        runs_col = 'runs_off_bat' if 'runs_off_bat' in df.columns else ('batsman_runs' if 'batsman_runs' in df.columns else 'runs_of_bat')

        def get_batter_stats(name):
            b_df = df[df[batter_col] == name]
            if b_df.empty:
                return None
            balls = len(b_df)
            runs = int(b_df[runs_col].sum())
            outs = int(b_df['is_wicket'].sum()) if 'is_wicket' in b_df.columns else 1
            outs = max(1, outs)
            avg = round(runs / outs, 2)
            sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0

            fours = int((b_df['is_four'] == 1).sum()) if 'is_four' in b_df.columns else int((b_df[runs_col] == 4).sum())
            sixes = int((b_df['is_six'] == 1).sum()) if 'is_six' in b_df.columns else int((b_df[runs_col] == 6).sum())
            dots = int((b_df[runs_col] == 0).sum())
            dot_pct = round((dots / balls) * 100, 1) if balls > 0 else 0.0

            return {
                "name": name,
                "runs": runs,
                "balls": balls,
                "sr": sr,
                "avg": avg,
                "fours": fours,
                "sixes": sixes,
                "dots": dots,
                "dot_pct": dot_pct
            }

        s1 = get_batter_stats(p1_name)
        s2 = get_batter_stats(p2_name)

        if not s1 and not s2:
            return f"⚠️ Players '{player1}' and '{player2}' were not found in dataset.", {}
        if not s1:
            return f"⚠️ Player '{player1}' was not found in dataset.", {}
        if not s2:
            return f"⚠️ Player '{player2}' was not found in dataset.", {}

        report = (
            f"⚔️ <b>Side-by-Side Analytics: {s1['name']} vs {s2['name']}</b><br><br>"
            f"<b>📊 {s1['name']}</b>:<br>"
            f"• Runs: <b>{s1['runs']:,}</b> ({s1['balls']:,} balls)<br>"
            f"• Strike Rate: <b>{s1['sr']}</b> | Average: <b>{s1['avg']}</b><br>"
            f"• Boundaries: <b>{s1['fours']} Fours</b> | <b>{s1['sixes']} Sixes</b><br>"
            f"• Dot Ball %: <b>{s1['dot_pct']}%</b><br><br>"
            f"<b>📊 {s2['name']}</b>:<br>"
            f"• Runs: <b>{s2['runs']:,}</b> ({s2['balls']:,} balls)<br>"
            f"• Strike Rate: <b>{s2['sr']}</b> | Average: <b>{s2['avg']}</b><br>"
            f"• Boundaries: <b>{s2['fours']} Fours</b> | <b>{s2['sixes']} Sixes</b><br>"
            f"• Dot Ball %: <b>{s2['dot_pct']}%</b><br><br>"
            f"💡 <i>Insight: {s1['name'] if s1['sr'] > s2['sr'] else s2['name']} leads in Strike Rate ({max(s1['sr'], s2['sr'])} vs {min(s1['sr'], s2['sr'])}).</i>"
        )

        navigation = {
            "target_section": "👤 Player Stats",
            "selected_player1": s1['name'],
            "selected_player2": s2['name'],
            "p1_stats": s1,
            "p2_stats": s2
        }
        return report, navigation

    @classmethod
    def get_bowler_telemetry_report(cls, bowler_name: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Extract REAL Hawk-Eye delivery telemetry metrics for a bowler."""
        real_bowler = cls._find_player(df, bowler_name)
        from ipl_analytics.charts.bowling import calculate_bowler_telemetry_averages
        stats = calculate_bowler_telemetry_averages(df, real_bowler)

        report = (
            f"⚡ <b>{stats['bowler']} — Hawk-Eye Delivery Telemetry:</b><br><br>"
            f"• Average Speed: <b>{stats['avg_speed']} km/h</b> (Peak: <b>{stats['max_speed']} km/h</b>)<br>"
            f"• Air Swing Movement: <b>{stats['avg_swing']} cm</b><br>"
            f"• Off-Pitch Seam Deviation: <b>{stats['avg_deviation']} cm</b><br>"
            f"• Pitch Bounce Distance: <b>{stats['avg_bounce_length']} m</b><br>"
            f"• Stumps Target Zone: <b>{stats['stumps_target_zone']}</b><br>"
            f"• Tracking Deliveries Analyzed: <b>{stats['total_deliveries']:,}</b><br><br>"
            f"💡 <i>Telemetry Engine: {'Real Hawk-Eye Spatial Coordinates' if stats['is_real_hawkeye'] else 'Statistical Pattern Generator'}.</i>"
        )

        navigation = {
            "target_section": "🎬 Animations",
            "selected_bowler": stats['bowler']
        }
        return report, navigation

    @classmethod
    def get_bowler_phase_stats(cls, bowler_name: str, phase_query: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Extract exact bowler performance in specific phases (Powerplay, Middle, Death)."""
        if df is None or df.empty:
            return "⚠️ No dataset loaded for bowler analysis.", {}

        real_bowler = cls._find_player(df, bowler_name)
        b_df = df[df['bowler'] == real_bowler]

        if b_df.empty:
            return f"⚠️ Bowler '{bowler_name}' not found in dataset.", {}

        phase_str = str(phase_query).lower()
        if 'death' in phase_str or '16' in phase_str:
            target_phase = 'Death (16-20)'
            phase_df = b_df[b_df['over'] >= 16] if 'over' in b_df.columns else b_df
        elif 'powerplay' in phase_str or '1-6' in phase_str or 'early' in phase_str:
            target_phase = 'Powerplay (1-6)'
            phase_df = b_df[b_df['over'] <= 6] if 'over' in b_df.columns else b_df
        else:
            target_phase = 'Middle (7-15)'
            phase_df = b_df[(b_df['over'] >= 7) & (b_df['over'] <= 15)] if 'over' in b_df.columns else b_df

        balls = len(phase_df)
        if balls == 0:
            return f"⚠️ No delivery records found for {real_bowler} in {target_phase}.", {}

        overs = round(balls / 6, 1)
        runs = int(phase_df['total_runs'].sum()) if 'total_runs' in phase_df.columns else int(phase_df['runs_off_bat'].sum())
        wickets = int(phase_df['is_wicket'].sum()) if 'is_wicket' in phase_df.columns else 0
        econ = round((runs / overs), 2) if overs > 0 else 0.0

        runs_col = 'runs_off_bat' if 'runs_off_bat' in phase_df.columns else 'total_runs'
        dots = int((phase_df[runs_col] == 0).sum())
        dot_pct = round((dots / balls) * 100, 1) if balls > 0 else 0.0

        report = (
            f"🎯 <b>{real_bowler} — {target_phase} Telemetry:</b><br><br>"
            f"• Overs Bowled: <b>{overs} overs</b> ({balls} deliveries)<br>"
            f"• Wickets Taken: <b>{wickets} wickets</b><br>"
            f"• Runs Conceded: <b>{runs} runs</b><br>"
            f"• Economy Rate: <b>{econ} RPO</b><br>"
            f"• Dot Ball Count: <b>{dots} dots</b> ({dot_pct}%)<br><br>"
            f"💡 <i>Tactical Rating: {'Outstanding containment' if econ < 8.0 else 'High boundary vulnerability'} in {target_phase}.</i>"
        )

        navigation = {
            "target_section": "🎳 Bowling Analysis",
            "selected_bowler": real_bowler
        }
        return report, navigation

    @classmethod
    def filter_team_season(cls, team_query: str, season_query: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Filter dashboard by team and season."""
        team_name = team_query
        season_val = season_query

        report = (
            f"🔍 <b>Filter Command Executed:</b><br>"
            f"• Selected Team: <b>{team_name}</b><br>"
            f"• Selected Season: <b>{season_val}</b><br><br>"
            f"Dashboard view updated with targeted telemetry."
        )

        navigation = {
            "target_section": "📊 Phase Analysis",
            "selected_team": team_name,
            "selected_season": season_val
        }
        return report, navigation

    @classmethod
    def navigate_to_module(cls, query: str) -> Tuple[str, Dict[str, Any]]:
        """Navigate dashboard to requested module."""
        q = str(query).lower()

        if any(k in q for k in ['pitch', 'length', '3d pitch', 'good length', 'yorker', 'wagon', 'wheel']):
            target = "🎯 Pitch Maps & Wagon Wheel"
        elif any(k in q for k in ['phase', 'powerplay', 'death', 'middle', 'over']):
            target = "📊 Phase Analysis"
        elif any(k in q for k in ['player', 'impact', 'rating', 'compare', 'versus']):
            target = "👤 Player Stats"
        elif any(k in q for k in ['bowling', 'bowler', 'economy']):
            target = "🎳 Bowling Analysis"
        elif any(k in q for k in ['hawkeye', 'tracking', 'telemetry', 'speed', 'bounce', 'ball']):
            target = "📊 Ball Tracking"
        elif any(k in q for k in ['anim', 'animated', 'trajectory', '3d anim']):
            target = "🎬 Animations"
        else:
            target = "👤 Player Stats"

        report = f"🚀 Navigated to <b>{target}</b> module."
        navigation = {"target_section": target}
        return report, navigation


def process_copilot_command(user_query: str, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
    """
    Parses user natural language query, invokes appropriate analytics tool,
    returns formatted report & navigation instructions.
    """
    q = str(user_query).strip()
    q_lower = q.lower()

    # 1. Check for Player Comparison Intent (e.g. "Compare Gaikwad vs Gill", "Suryakumar Yadav vs Bumrah")
    vs_match = re.search(r'(?:compare\s+)?([a-zA-Z\s]+)\s+(?:vs|versus|against|\&)\s+([a-zA-Z\s]+)', q, re.IGNORECASE)
    if vs_match:
        p1 = vs_match.group(1).replace('compare', '').strip()
        p2 = vs_match.group(2).strip()
        if len(p1) > 2 and len(p2) > 2:
            return AnalyticsToolRegistry.compare_players(p1, p2, df)

    # 2. Check for Hawk-Eye Telemetry Intent (e.g. "Suryakumar Yadav speed", "Bumrah swing telemetry")
    telemetry_keywords = ['speed', 'swing', 'deviation', 'bounce', 'target zone', 'hawkeye', 'telemetry', 'release speed']
    if any(k in q_lower for k in telemetry_keywords):
        words = [w for w in q.split() if w.lower() not in [
            'show', 'display', 'get', 'the', 'in', 'speed', 'swing', 'deviation', 'bounce', 'target',
            'zone', 'hawkeye', 'telemetry', 'release', 'radar', 'stats', 'statistics', 'for', 'of',
            'and', 'with', 'also', 'data', '&'
        ]]
        if words:
            player_name = " ".join(words)
            return AnalyticsToolRegistry.get_bowler_telemetry_report(player_name, df)

    # 3. Check for Bowler Phase Stats Intent (e.g. "Bumrah death overs", "Show Chahal powerplay stats")
    bowler_keywords = ['death', 'powerplay', 'middle', 'overs', 'stat', 'economy']
    if any(k in q_lower for k in bowler_keywords):
        words = [w for w in q.split() if w.lower() not in [
            'show', 'display', 'get', 'the', 'in', 'overs', 'death', 'powerplay', 'middle',
            'statistics', 'stats', 'for', 'of', 'performance'
        ]]
        if words:
            bowler_name = " ".join(words)
            return AnalyticsToolRegistry.get_bowler_phase_stats(bowler_name, q_lower, df)

    # 4. Check for Navigation Intent
    nav_keywords = ['show', 'open', 'display', 'go to', 'navigate', 'view']
    if any(q_lower.startswith(k) for k in nav_keywords) or 'map' in q_lower or 'wheel' in q_lower:
        return AnalyticsToolRegistry.navigate_to_module(q_lower)

    # Default fallback: check if single player queried (e.g. "Suryakumar Yadav")
    words = [w for w in q.split() if w.lower() not in ['show', 'get', 'view', 'stat', 'stats', 'player']]
    if len(words) >= 1:
        p_candidate = " ".join(words)
        found = AnalyticsToolRegistry._find_player(df, p_candidate)
        if found and found != p_candidate:
            return AnalyticsToolRegistry.get_bowler_telemetry_report(found, df)

    return AnalyticsToolRegistry.navigate_to_module(q_lower)
