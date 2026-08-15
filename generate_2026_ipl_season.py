"""
IPL 2026 Season Dataset Generator & Pipeline Integrator
Generates a complete, realistic 2026 IPL Season match dataset (74 matches, ~17,500 ball-by-ball deliveries)
and merges it into all_ipl_matches.parquet, all_ipl_matches.csv, and hawkeye_simulated_2022_2026.csv.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).parent
PARQUET_PATH = BASE_DIR / "all_ipl_matches.parquet"
CSV_PATH = BASE_DIR / "all_ipl_matches.csv"
HAWKEYE_SIM_PATH = BASE_DIR / "hawkeye_simulated_2022_2026.csv"

# Active 10 IPL Franchises & Rosters
TEAMS = [
    'Chennai Super Kings', 'Delhi Capitals', 'Gujarat Titans',
    'Kolkata Knight Riders', 'Lucknow Super Giants', 'Mumbai Indians',
    'Punjab Kings', 'Rajasthan Royals', 'Royal Challengers Bengaluru', 'Sunrisers Hyderabad'
]

VENUES = [
    'M Chinnaswamy Stadium', 'MA Chidambaram Stadium, Chepauk', 'Wankhede Stadium',
    'Eden Gardens', 'Narendra Modi Stadium', 'Rajiv Gandhi International Stadium, Uppal',
    'Arun Jaitley Stadium', 'Sawai Mansingh Stadium', 'Maharashtra Cricket Association Stadium',
    'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium'
]

BATTERS = {
    'Chennai Super Kings': ['RD Gaikwad', 'DP Conway', 'D Mitchell', 'S Dube', 'MS Dhoni', 'RA Jadeja', 'R Rachindra'],
    'Mumbai Indians': ['RG Sharma', 'Ishan Kishan', 'SA Yadav', 'HH Pandya', 'T David', 'N Tilak Varma', 'R Shepherd'],
    'Royal Challengers Bengaluru': ['V Kohli', 'F du Plessis', 'RM Patidar', 'GJ Maxwell', 'KD Karthik', 'C Green', 'AS Joseph'],
    'Kolkata Knight Riders': ['PD Salt', 'SP Narine', 'V Iyer', 'SS Iyer', 'Rinku Singh', 'AD Russell', 'Ramandeep Singh'],
    'Gujarat Titans': ['Shubman Gill', 'B Sai Sudharsan', 'DA Miller', 'V Shankar', 'R Tewatia', 'M Shahrukh Khan', 'A Manohar'],
    'Rajasthan Royals': ['YBK Jaiswal', 'JC Buttler', 'SV Samson', 'R Parag', 'SO Hetmyer', 'D Jurel', 'R Ashwin'],
    'Sunrisers Hyderabad': ['TM Head', 'Abhishek Sharma', 'AK Markram', 'H Klaasen', 'NK Reddy', 'Abdul Samad', 'PJ Cummins'],
    'Delhi Capitals': ['Prithvi Shaw', 'J Fraser-McGurk', 'AR Patel', 'RR Pant', 'T Stubbs', 'Abishek Porel', 'K Kushagra'],
    'Lucknow Super Giants': ['KL Rahul', 'Q de Kock', 'D Hooda', 'MP Stoinis', 'N Pooran', 'K Pandya', 'Ayush Badoni'],
    'Punjab Kings': ['S Dhawan', 'JM Bairstow', 'P Simran Singh', 'SM Curran', 'JM Sharma', 'L Livingstone', 'Ashutosh Sharma']
}

BOWLERS = {
    'Chennai Super Kings': ['M Pathirana', 'DL Chahar', 'TU Deshpande', 'RA Jadeja', 'M Theekshana', 'Shardul Thakur'],
    'Mumbai Indians': ['JJ Bumrah', 'G Coetzee', 'N Thushara', 'P Chawla', 'HH Pandya', 'KW Richardson'],
    'Royal Challengers Bengaluru': ['Mohammed Siraj', 'Y Dayal', 'KV Sharma', 'C Green', 'AS Joseph', 'Mayank Dagar'],
    'Kolkata Knight Riders': ['MA Starc', 'HV Patel', 'SP Narine', 'CV Varun', 'AD Russell', 'Vaibhav Arora'],
    'Gujarat Titans': ['Rashid Khan', 'Mohammed Shami', 'SP Johnson', 'M Sharma', 'R Sai Kishore', 'AZ Joseph'],
    'Rajasthan Royals': ['YS Chahal', 'TA Boult', 'A Avesh Khan', 'S Sandeep Sharma', 'R Ashwin', 'KM Asif'],
    'Sunrisers Hyderabad': ['PJ Cummins', 'B Kumar', 'T Natarajan', 'M Markande', 'W Sundar', 'Jaydev Unadkat'],
    'Delhi Capitals': ['Kuldeep Yadav', 'K Rabada', 'KK Ahmed', 'AR Patel', 'Mukesh Kumar', 'Iant Sharma'],
    'Lucknow Super Giants': ['Mayank Yadav', 'R Bishnoi', 'Naveen-ul-Haq', 'K Pandya', 'Yash Thakur', 'Mohsin Khan'],
    'Punjab Kings': ['Arshdeep Singh', 'K Rabada', 'HV Patel', 'SM Curran', 'RD Chahar', 'Rahul Chahar']
}


def generate_2026_matches():
    """Generate 74 complete 2026 IPL matches with ball-by-ball scorecards."""
    logging.info("Generating complete 2026 IPL Season match dataset (74 matches)...")
    np.random.seed(2026)

    deliveries = []
    match_id_base = 2026001

    for m_idx in range(1, 75):
        match_id = match_id_base + m_idx - 1
        t1, t2 = np.random.choice(TEAMS, size=2, replace=False)
        venue = np.random.choice(VENUES)

        t1_batters = BATTERS[t1]
        t2_batters = BATTERS[t2]
        t1_bowlers = BOWLERS[t1]
        t2_bowlers = BOWLERS[t2]

        # Innings 1 (t1 bats, t2 bowls)
        b_idx = 0
        w_count = 0
        current_striker = t1_batters[0]
        current_non_striker = t1_batters[1]

        for over in range(20):
            bowler = np.random.choice(t2_bowlers)
            for ball_in_over in range(1, 7):
                ball_val = float(f"{over}.{ball_in_over}")
                
                # Determine outcome
                rand = np.random.random()
                if rand < 0.05 and w_count < 9:
                    wicket = 1
                    wicket_type = np.random.choice(['caught', 'bowled', 'lbw', 'run out'])
                    player_dismissed = current_striker
                    runs = 0
                    w_count += 1
                    if b_idx + 2 < len(t1_batters):
                        b_idx += 1
                        current_striker = t1_batters[b_idx + 1]
                else:
                    wicket = 0
                    wicket_type = None
                    player_dismissed = None
                    runs = np.random.choice([0, 1, 2, 4, 6], p=[0.40, 0.35, 0.08, 0.12, 0.05])

                extras = 1 if np.random.random() < 0.04 else 0
                wides = extras if extras and np.random.random() < 0.7 else 0
                noballs = extras - wides

                deliveries.append({
                    'match_id': match_id,
                    'season': '2026',
                    'innings': 1,
                    'over': over + 1,
                    'ball': ball_val,
                    'batting_team': t1,
                    'bowling_team': t2,
                    'venue': venue,
                    'striker': current_striker,
                    'non_striker': current_non_striker,
                    'bowler': bowler,
                    'runs_off_bat': runs,
                    'extras': extras,
                    'wides': wides,
                    'noballs': noballs,
                    'byes': 0,
                    'legbyes': 0,
                    'penalty': 0,
                    'total_runs': runs + extras,
                    'is_wicket': wicket,
                    'wicket_type': wicket_type or '',
                    'player_dismissed': player_dismissed or '',
                    'is_bowler_wicket': 1 if wicket and wicket_type != 'run out' else 0,
                    'phase': 'Powerplay' if over < 6 else ('Middle Overs' if over < 15 else 'Death Overs'),
                    'legal_ball': 1 if extras == 0 else 0,
                    'boundary': 1 if runs in [4, 6] else 0,
                    'dot_ball': 1 if (runs == 0 and extras == 0) else 0,
                    'is_four': 1 if runs == 4 else 0,
                    'is_six': 1 if runs == 6 else 0
                })

                if runs % 2 == 1:
                    current_striker, current_non_striker = current_non_striker, current_striker

            current_striker, current_non_striker = current_non_striker, current_striker

        # Innings 2 (t2 bats, t1 bowls)
        b_idx = 0
        w_count = 0
        current_striker = t2_batters[0]
        current_non_striker = t2_batters[1]

        for over in range(20):
            bowler = np.random.choice(t1_bowlers)
            for ball_in_over in range(1, 7):
                ball_val = float(f"{over}.{ball_in_over}")
                rand = np.random.random()
                if rand < 0.05 and w_count < 9:
                    wicket = 1
                    wicket_type = np.random.choice(['caught', 'bowled', 'lbw', 'run out'])
                    player_dismissed = current_striker
                    runs = 0
                    w_count += 1
                    if b_idx + 2 < len(t2_batters):
                        b_idx += 1
                        current_striker = t2_batters[b_idx + 1]
                else:
                    wicket = 0
                    wicket_type = None
                    player_dismissed = None
                    runs = np.random.choice([0, 1, 2, 4, 6], p=[0.40, 0.35, 0.08, 0.12, 0.05])

                extras = 1 if np.random.random() < 0.04 else 0
                wides = extras if extras and np.random.random() < 0.7 else 0
                noballs = extras - wides

                deliveries.append({
                    'match_id': match_id,
                    'season': '2026',
                    'innings': 2,
                    'over': over + 1,
                    'ball': ball_val,
                    'batting_team': t2,
                    'bowling_team': t1,
                    'venue': venue,
                    'striker': current_striker,
                    'non_striker': current_non_striker,
                    'bowler': bowler,
                    'runs_off_bat': runs,
                    'extras': extras,
                    'wides': wides,
                    'noballs': noballs,
                    'byes': 0,
                    'legbyes': 0,
                    'penalty': 0,
                    'total_runs': runs + extras,
                    'is_wicket': wicket,
                    'wicket_type': wicket_type or '',
                    'player_dismissed': player_dismissed or '',
                    'is_bowler_wicket': 1 if wicket and wicket_type != 'run out' else 0,
                    'phase': 'Powerplay' if over < 6 else ('Middle Overs' if over < 15 else 'Death Overs'),
                    'legal_ball': 1 if extras == 0 else 0,
                    'boundary': 1 if runs in [4, 6] else 0,
                    'dot_ball': 1 if (runs == 0 and extras == 0) else 0,
                    'is_four': 1 if runs == 4 else 0,
                    'is_six': 1 if runs == 6 else 0
                })

                if runs % 2 == 1:
                    current_striker, current_non_striker = current_non_striker, current_striker

            current_striker, current_non_striker = current_non_striker, current_striker

    df_2026 = pd.DataFrame(deliveries)
    logging.info(f"Generated {len(df_2026):,} deliveries for 2026 season.")
    return df_2026


def integrate_2026_season():
    """Merge 2026 dataset into parquet and csv files."""
    df_2026 = generate_2026_matches()

    if PARQUET_PATH.exists():
        existing_df = pd.read_parquet(PARQUET_PATH)
        # Ensure season data types match
        existing_df['season'] = pd.to_numeric(existing_df['season'], errors='coerce')
        df_2026['season'] = pd.to_numeric(df_2026['season'], errors='coerce')
        # Remove old 2026 if present
        existing_df = existing_df[existing_df['season'] != 2026]
        combined_df = pd.concat([existing_df, df_2026], ignore_index=True)
    else:
        combined_df = df_2026
        combined_df['season'] = pd.to_numeric(combined_df['season'], errors='coerce')

    # Save Parquet & CSV
    combined_df.to_parquet(PARQUET_PATH, index=False)
    combined_df.to_csv(CSV_PATH, index=False)
    logging.info(f"✅ Successfully integrated 2026 IPL Season! Total dataset size: {len(combined_df):,} deliveries.")

    # Re-run vectorized telemetry enrichment to generate Hawk-Eye 3D coordinates for 2026
    import enrich_dataset_values
    enrich_dataset_values.clean_match_dataset()
    enrich_dataset_values.simulate_missing_hawkeye_telemetry()
    logging.info("🎉 2026 IPL Season Dataset Pipeline Complete!")


if __name__ == "__main__":
    integrate_2026_season()
