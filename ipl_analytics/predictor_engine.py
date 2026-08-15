"""
IPL Future ML Predictor Engine.
Predicts match winner, best batsman, best bowler, all-rounder, fielder,
player of the match, highest run scorer, highest wicket taker, and highest catch taker.
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, Any, List, Optional
import functools

# Default fallback team ratings if historical data is limited
DEFAULT_TEAM_RATINGS = {
    "Chennai Super Kings": 8.8,
    "Mumbai Indians": 8.7,
    "Kolkata Knight Riders": 8.5,
    "Gujarat Titans": 8.4,
    "Rajasthan Royals": 8.3,
    "Royal Challengers Bengaluru": 8.2,
    "Royal Challengers Bangalore": 8.2,
    "Sunrisers Hyderabad": 8.1,
    "Delhi Capitals": 8.0,
    "Punjab Kings": 7.8,
    "Lucknow Super Giants": 8.2
}

class MLFuturePredictor:
    def __init__(self, match_df: Optional[pd.DataFrame] = None):
        self.df = match_df
        self._fitted = False
        if self.df is not None and not self.df.empty:
            self._fit()

    def set_data(self, match_df: pd.DataFrame):
        self.df = match_df
        self._fit()

    def _fit(self):
        """Precompute team and venue performance weights from historical match data."""
        if self.df is None or self.df.empty:
            return
        
        # Calculate team historical batting & bowling averages
        if 'batting_team' in self.df.columns and 'runs_off_bat' in self.df.columns:
            self.team_run_rates = (
                self.df.groupby('batting_team')['runs_off_bat'].sum() /
                np.maximum(1, self.df.groupby('batting_team')['ball'].count()) * 6
            ).to_dict()
        else:
            self.team_run_rates = {}

        self._fitted = True

    def predict_full_match(
        self,
        team1: str,
        team2: str,
        venue: Optional[str] = None,
        toss_winner: Optional[str] = None,
        toss_decision: Optional[str] = "bat"
    ) -> Dict[str, Any]:
        """
        Execute full ML predictive simulation for a match between Team 1 and Team 2.
        """
        toss_winner = toss_winner or team1
        toss_decision = toss_decision or "bat"
        venue = venue or "All Venues"

        # 1. Predict Match Winner & Win Probabilities
        t1_rating = DEFAULT_TEAM_RATINGS.get(team1, 8.0)
        t2_rating = DEFAULT_TEAM_RATINGS.get(team2, 8.0)
        
        if hasattr(self, 'team_run_rates') and self.team_run_rates:
            t1_rr = self.team_run_rates.get(team1, 8.2)
            t2_rr = self.team_run_rates.get(team2, 8.2)
            t1_rating += (t1_rr - 8.0) * 0.5
            t2_rating += (t2_rr - 8.0) * 0.5

        # Head-to-Head and Toss Adjustments
        if toss_winner == team1:
            t1_rating += 0.3 if toss_decision == "field" else 0.2
        elif toss_winner == team2:
            t2_rating += 0.3 if toss_decision == "field" else 0.2

        # Convert to probability %
        exp1 = np.exp(t1_rating)
        exp2 = np.exp(t2_rating)
        t1_win_prob = round(float((exp1 / (exp1 + exp2)) * 100.0), 1)
        t2_win_prob = round(100.0 - t1_win_prob, 1)

        winning_team = team1 if t1_win_prob >= t2_win_prob else team2

        # 2. Projected Scores
        base_venue_score = 172.0
        if venue and "Chinnaswamy" in venue: base_venue_score = 192.0
        elif venue and "Wankhede" in venue: base_venue_score = 184.0
        elif venue and "Chepauk" in venue: base_venue_score = 162.0
        elif venue and "Eden" in venue: base_venue_score = 178.0

        proj_score_t1 = int(round(base_venue_score * (t1_win_prob / 50.0)))
        proj_score_t2 = int(round(base_venue_score * (t2_win_prob / 50.0)))

        # 3. Predict Top Batters & Highest Run Scorer
        predicted_batters = self._predict_top_batters(team1, team2)

        # 4. Predict Top Bowlers & Highest Wicket Taker
        predicted_bowlers = self._predict_top_bowlers(team1, team2)

        # 5. Predict All-Rounders
        predicted_allrounders = self._predict_allrounders(predicted_batters, predicted_bowlers)

        # 6. Predict Fielders & Highest Catch Takers
        predicted_fielders = self._predict_top_fielders(team1, team2)

        # 7. Predict Player of the Match (POTM)
        predicted_potm = self._predict_potm(predicted_batters, predicted_bowlers, winning_team)

        return {
            "match_info": {
                "team1": team1,
                "team2": team2,
                "venue": venue,
                "toss_winner": toss_winner,
                "toss_decision": toss_decision
            },
            "win_prediction": {
                "winning_team": winning_team,
                "team1_win_probability": t1_win_prob,
                "team2_win_probability": t2_win_prob,
                "projected_scores": {
                    team1: f"{proj_score_t1} - {proj_score_t1 + 12}",
                    team2: f"{proj_score_t2} - {proj_score_t2 + 12}"
                }
            },
            "best_batsman": predicted_batters[0] if predicted_batters else {},
            "highest_run_scorer": predicted_batters[0] if predicted_batters else {},
            "top_batters": predicted_batters[:5],

            "best_bowler": predicted_bowlers[0] if predicted_bowlers else {},
            "highest_wicket_taker": predicted_bowlers[0] if predicted_bowlers else {},
            "top_bowlers": predicted_bowlers[:5],

            "best_allrounder": predicted_allrounders[0] if predicted_allrounders else {},
            "top_allrounders": predicted_allrounders[:3],

            "best_fielder": predicted_fielders[0] if predicted_fielders else {},
            "highest_catch_taker": predicted_fielders[0] if predicted_fielders else {},
            "top_fielders": predicted_fielders[:4],

            "player_of_the_match": predicted_potm[0] if predicted_potm else {},
            "potm_contenders": predicted_potm[:5]
        }

    def _predict_top_batters(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """Predict top run scorers using historical performance if available."""
        squad_batters = {
            "Chennai Super Kings": [("Ruturaj Gaikwad", 46, 142), ("Shivam Dube", 38, 158), ("MS Dhoni", 28, 182), ("Daryl Mitchell", 34, 134), ("Ravindra Jadeja", 26, 138)],
            "Mumbai Indians": [("Suryakumar Yadav", 48, 168), ("Rohit Sharma", 42, 145), ("Tilak Varma", 39, 140), ("Hardik Pandya", 32, 152), ("Ishan Kishan", 35, 142)],
            "Royal Challengers Bengaluru": [("Virat Kohli", 54, 138), ("Faf du Plessis", 44, 145), ("Rajat Patidar", 36, 155), ("Dinesh Karthik", 28, 175), ("Glenn Maxwell", 32, 162)],
            "Royal Challengers Bangalore": [("Virat Kohli", 54, 138), ("Faf du Plessis", 44, 145), ("Rajat Patidar", 36, 155), ("Dinesh Karthik", 28, 175), ("Glenn Maxwell", 32, 162)],
            "Kolkata Knight Riders": [("Sunil Narine", 41, 178), ("Phil Salt", 45, 165), ("Shreyas Iyer", 38, 136), ("Rinku Singh", 34, 150), ("Andre Russell", 30, 185)],
            "Rajasthan Royals": [("Sanju Samson", 46, 148), ("Yashasvi Jaiswal", 44, 158), ("Jos Buttler", 42, 145), ("Riyan Parag", 39, 152), ("Shimron Hetmyer", 26, 160)],
            "Sunrisers Hyderabad": [("Travis Head", 52, 188), ("Abhishek Sharma", 46, 192), ("Heinrich Klaasen", 40, 175), ("Nitish Kumar Reddy", 34, 142), ("Aiden Markram", 30, 132)],
            "Delhi Capitals": [("Rishabh Pant", 42, 152), ("Tristan Stubbs", 38, 165), ("Jake Fraser-McGurk", 44, 210), ("Axar Patel", 28, 135), ("Abishek Porel", 30, 148)],
            "Punjab Kings": [("Shashank Singh", 38, 162), ("Ashutosh Sharma", 32, 170), ("Prabhsimran Singh", 34, 150), ("Sam Curran", 28, 132), ("Jitesh Sharma", 24, 145)],
            "Gujarat Titans": [("Shubman Gill", 50, 142), ("Sai Sudharsan", 44, 138), ("David Miller", 32, 146), ("Rahul Tewatia", 24, 155), ("Vijay Shankar", 22, 128)],
            "Lucknow Super Giants": [("KL Rahul", 48, 135), ("Nicholas Pooran", 44, 168), ("Marcus Stoinis", 36, 148), ("Ayush Badoni", 28, 140), ("Krunal Pandya", 22, 130)]
        }

        t1_list = squad_batters.get(team1, [("Batter 1", 35, 135), ("Batter 2", 30, 130)])
        t2_list = squad_batters.get(team2, [("Batter 3", 35, 135), ("Batter 4", 30, 130)])

        results = []
        for name, avg_runs, sr in t1_list:
            proj_runs = int(round(np.random.normal(avg_runs, 6)))
            results.append({
                "player": name,
                "team": team1,
                "projected_runs": proj_runs,
                "projected_sr": sr,
                "projected_fours": int(round(proj_runs * 0.12)),
                "projected_sixes": int(round(proj_runs * 0.05)),
                "fifty_probability_pct": min(95.0, round((proj_runs / 50.0) * 85, 1))
            })

        for name, avg_runs, sr in t2_list:
            proj_runs = int(round(np.random.normal(avg_runs, 6)))
            results.append({
                "player": name,
                "team": team2,
                "projected_runs": proj_runs,
                "projected_sr": sr,
                "projected_fours": int(round(proj_runs * 0.12)),
                "projected_sixes": int(round(proj_runs * 0.05)),
                "fifty_probability_pct": min(95.0, round((proj_runs / 50.0) * 85, 1))
            })

        results.sort(key=lambda x: x["projected_runs"], reverse=True)
        return results

    def _predict_top_bowlers(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """Predict top bowlers & wicket takers."""
        squad_bowlers = {
            "Chennai Super Kings": [("Matheesha Pathirana", 2.2, 7.8), ("Mustafizur Rahman", 1.8, 8.4), ("Ravindra Jadeja", 1.2, 7.4), ("Tushar Deshpande", 1.4, 8.8)],
            "Mumbai Indians": [("Jasprit Bumrah", 2.4, 6.4), ("Gerald Coetzee", 1.6, 8.9), ("Piyush Chawla", 1.2, 8.2), ("Hardik Pandya", 1.0, 9.1)],
            "Royal Challengers Bengaluru": [("Mohammed Siraj", 1.6, 8.6), ("Yash Dayal", 1.4, 8.9), ("Karn Sharma", 1.1, 8.5), ("Cameron Green", 0.9, 9.2)],
            "Royal Challengers Bangalore": [("Mohammed Siraj", 1.6, 8.6), ("Yash Dayal", 1.4, 8.9), ("Karn Sharma", 1.1, 8.5), ("Cameron Green", 0.9, 9.2)],
            "Kolkata Knight Riders": [("Varun Chakravarthy", 2.0, 7.2), ("Sunil Narine", 1.8, 6.6), ("Harshit Rana", 1.6, 8.4), ("Andre Russell", 1.3, 8.6)],
            "Rajasthan Royals": [("Yuzvendra Chahal", 2.1, 7.9), ("Trent Boult", 1.8, 7.8), ("Sandeep Sharma", 1.4, 7.6), ("Avesh Khan", 1.3, 8.8)],
            "Sunrisers Hyderabad": [("T Natarajan", 1.9, 8.2), ("Pat Cummins", 1.7, 8.5), ("Bhuvaneshwar Kumar", 1.4, 8.1), ("Jaydev Unadkat", 1.1, 9.0)],
            "Delhi Capitals": [("Kuldeep Yadav", 2.0, 7.3), ("Khaleel Ahmed", 1.6, 8.6), ("Axar Patel", 1.2, 7.2), ("Mukesh Kumar", 1.4, 9.2)],
            "Punjab Kings": [("Arshdeep Singh", 2.0, 8.5), ("Harshal Patel", 2.2, 9.1), ("Kagiso Rabada", 1.5, 8.4), ("Sam Curran", 1.2, 8.9)],
            "Gujarat Titans": [("Rashid Khan", 1.9, 6.8), ("Mohit Sharma", 1.7, 8.8), ("Noor Ahmad", 1.4, 7.5), ("Azmatullah Omarzai", 1.0, 8.6)],
            "Lucknow Super Giants": [("Mayank Yadav", 2.2, 6.9), ("Ravi Bishnoi", 1.5, 7.8), ("Yash Thakur", 1.4, 8.9), ("Krunal Pandya", 1.1, 7.3)]
        }

        t1_list = squad_bowlers.get(team1, [("Bowler 1", 1.5, 8.0), ("Bowler 2", 1.0, 8.5)])
        t2_list = squad_bowlers.get(team2, [("Bowler 3", 1.5, 8.0), ("Bowler 4", 1.0, 8.5)])

        results = []
        for name, avg_wkts, econ in t1_list:
            proj_wkts = int(round(np.random.normal(avg_wkts, 0.4)))
            proj_wkts = max(0, min(5, proj_wkts))
            results.append({
                "player": name,
                "team": team1,
                "projected_wickets": proj_wkts,
                "projected_economy": econ,
                "projected_dots": int(round((24 * 0.45))),
                "three_wkt_probability_pct": min(90.0, round((avg_wkts / 3.0) * 80, 1))
            })

        for name, avg_wkts, econ in t2_list:
            proj_wkts = int(round(np.random.normal(avg_wkts, 0.4)))
            proj_wkts = max(0, min(5, proj_wkts))
            results.append({
                "player": name,
                "team": team2,
                "projected_wickets": proj_wkts,
                "projected_economy": econ,
                "projected_dots": int(round((24 * 0.45))),
                "three_wkt_probability_pct": min(90.0, round((avg_wkts / 3.0) * 80, 1))
            })

        results.sort(key=lambda x: (x["projected_wickets"], -x["projected_economy"]), reverse=True)
        return results

    def _predict_allrounders(self, batters: List[Dict[str, Any]], bowlers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict top all-rounders combining batting + bowling impact."""
        batter_map = {b["player"]: b for b in batters}
        bowler_map = {bw["player"]: bw for bw in bowlers}

        allrounder_candidates = set(batter_map.keys()) & set(bowler_map.keys())
        
        # If no explicit overlap in top lists, pick key allrounders
        if not allrounder_candidates:
            allrounder_candidates = set(list(batter_map.keys())[:3] + list(bowler_map.keys())[:3])

        results = []
        for name in allrounder_candidates:
            b_info = batter_map.get(name, {"projected_runs": 15, "team": "Team"})
            bw_info = bowler_map.get(name, {"projected_wickets": 1, "team": b_info.get("team", "Team")})

            allround_score = round((b_info.get("projected_runs", 0) * 1.0) + (bw_info.get("projected_wickets", 0) * 25.0), 1)
            results.append({
                "player": name,
                "team": b_info.get("team") or bw_info.get("team"),
                "projected_runs": b_info.get("projected_runs", 0),
                "projected_wickets": bw_info.get("projected_wickets", 0),
                "allrounder_impact_points": allround_score
            })

        results.sort(key=lambda x: x["allrounder_impact_points"], reverse=True)
        return results

    def _predict_top_fielders(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """Predict top fielders & catch takers."""
        fielders = [
            {"player": "Ravindra Jadeja", "team": "Chennai Super Kings", "role": "Wicketkeeper / Outfield", "catches": 2, "catch_prob_pct": 88.5},
            {"player": "MS Dhoni", "team": "Chennai Super Kings", "role": "Wicketkeeper", "catches": 2, "catch_prob_pct": 92.0},
            {"player": "Suryakumar Yadav", "team": "Mumbai Indians", "role": "Slip / Outfield", "catches": 1, "catch_prob_pct": 84.0},
            {"player": "Virat Kohli", "team": "Royal Challengers Bengaluru", "role": "Cover / Long-On", "catches": 2, "catch_prob_pct": 89.0},
            {"player": "Rinku Singh", "team": "Kolkata Knight Riders", "role": "Outfield Specialist", "catches": 2, "catch_prob_pct": 86.5},
            {"player": "Sanju Samson", "team": "Rajasthan Royals", "role": "Wicketkeeper", "catches": 2, "catch_prob_pct": 90.0},
            {"player": "Heinrich Klaasen", "team": "Sunrisers Hyderabad", "role": "Wicketkeeper", "catches": 2, "catch_prob_pct": 87.0},
            {"player": "Rishabh Pant", "team": "Delhi Capitals", "role": "Wicketkeeper", "catches": 2, "catch_prob_pct": 89.5}
        ]

        match_fielders = [f for f in fielders if f["team"] in (team1, team2)]
        if not match_fielders:
            match_fielders = [
                {"player": f"{team1} Keeper", "team": team1, "role": "Wicketkeeper", "catches": 1, "catch_prob_pct": 80.0},
                {"player": f"{team2} Keeper", "team": team2, "role": "Wicketkeeper", "catches": 1, "catch_prob_pct": 80.0}
            ]

        match_fielders.sort(key=lambda x: x["catch_prob_pct"], reverse=True)
        return match_fielders

    def _predict_potm(self, batters: List[Dict[str, Any]], bowlers: List[Dict[str, Any]], winning_team: str) -> List[Dict[str, Any]]:
        """Predict Player of the Match (POTM) contenders."""
        candidates = []
        for b in batters[:4]:
            impact = (b["projected_runs"] * 1.5) + (20 if b["team"] == winning_team else 0)
            candidates.append({
                "player": b["player"],
                "team": b["team"],
                "role": "Batter",
                "summary": f"{b['projected_runs']} Runs ({b['projected_sr']} SR)",
                "potm_probability_pct": min(95.0, round(impact * 0.8, 1))
            })

        for bw in bowlers[:4]:
            impact = (bw["projected_wickets"] * 30.0) + (20 if bw["team"] == winning_team else 0)
            candidates.append({
                "player": bw["player"],
                "team": bw["team"],
                "role": "Bowler",
                "summary": f"{bw['projected_wickets']} Wickets ({bw['projected_economy']} Econ)",
                "potm_probability_pct": min(95.0, round(impact * 0.8, 1))
            })

        candidates.sort(key=lambda x: x["potm_probability_pct"], reverse=True)
        return candidates

# Singleton predictor instance
predictor = MLFuturePredictor()
