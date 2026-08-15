import unittest
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ipl_analytics.predictor_engine import MLFuturePredictor

class TestPredictorEngine(unittest.TestCase):
    
    def test_predict_full_match(self):
        predictor = MLFuturePredictor()
        result = predictor.predict_full_match(
            team1="Chennai Super Kings",
            team2="Mumbai Indians",
            venue="Wankhede Stadium",
            toss_winner="Chennai Super Kings",
            toss_decision="bat"
        )
        
        self.assertIn("win_prediction", result)
        win_info = result["win_prediction"]
        self.assertIn("winning_team", win_info)
        self.assertIn(win_info["winning_team"], ["Chennai Super Kings", "Mumbai Indians"])
        self.assertGreaterEqual(win_info["team1_win_probability"], 0.0)
        self.assertLessEqual(win_info["team1_win_probability"], 100.0)

        # Verify best batter & highest run scorer
        self.assertIn("best_batsman", result)
        self.assertIn("player", result["best_batsman"])

        # Verify best bowler & highest wicket taker
        self.assertIn("best_bowler", result)
        self.assertIn("player", result["best_bowler"])

        # Verify best allrounder
        self.assertIn("best_allrounder", result)

        # Verify best fielder & catch taker
        self.assertIn("best_fielder", result)

        # Verify POTM contender
        self.assertIn("player_of_the_match", result)

if __name__ == '__main__':
    unittest.main()
