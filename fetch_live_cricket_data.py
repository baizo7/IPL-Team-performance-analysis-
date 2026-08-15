"""
Automated Cricsheet API & Web Scraper Script for IPL Analytics
Downloads the latest official Cricsheet IPL ball-by-ball zip archive,
parses new match data, and updates local dataset parquet and CSV files automatically.
"""
import os
import zipfile
import urllib.request
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).parent
CRICSHEET_IPL_URL = "https://cricsheet.org/downloads/ipl_male_csv2.zip"
ZIP_PATH = BASE_DIR / "ipl_male_csv2.zip"
PARQUET_PATH = BASE_DIR / "all_ipl_matches.parquet"
CSV_PATH = BASE_DIR / "all_ipl_matches.csv"


def download_latest_cricsheet_data():
    """Download the latest official IPL zip package from Cricsheet."""
    try:
        logging.info(f"Fetching latest IPL dataset from {CRICSHEET_IPL_URL}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(CRICSHEET_IPL_URL, headers=headers)
        with urllib.request.urlopen(req) as response, open(ZIP_PATH, 'wb') as out_file:
            out_file.write(response.read())
        logging.info(f"✅ Successfully downloaded {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / (1024*1024):.2f} MB)")
        return True
    except Exception as e:
        logging.error(f"Failed to download Cricsheet zip: {e}")
        return False


def extract_and_merge_cricsheet_matches():
    """Extract CSV files from zip and merge into all_ipl_matches.csv and parquet."""
    if not ZIP_PATH.exists():
        logging.warning("ZIP file not found. Skipping extraction.")
        return False

    temp_dir = BASE_DIR / "temp_cricsheet_extract"
    temp_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        csv_files = list(temp_dir.glob("*.csv"))
        logging.info(f"Found {len(csv_files)} match CSVs in Cricsheet package.")

        all_deliveries = []
        for f in csv_files:
            if f.name == "README.txt":
                continue
            try:
                m_df = pd.read_csv(f, low_memory=False)
                all_deliveries.append(m_df)
            except Exception:
                pass

        if not all_deliveries:
            logging.error("No valid CSV match data found.")
            return False

        merged_df = pd.concat(all_deliveries, ignore_index=True)

        # Standardize helper columns
        if 'season' in merged_df.columns:
            merged_df['season'] = merged_df['season'].astype(str).str.split('/').str[0]

        from ipl_data_cleaner import build_clean_dataset
        clean_df, report = build_clean_dataset(merged_df)

        # Save to Parquet & CSV
        clean_df.to_parquet(PARQUET_PATH, index=False)
        clean_df.to_csv(CSV_PATH, index=False)

        logging.info(f"✅ Successfully updated dataset! Total matches: {clean_df['match_id'].nunique():,}, Total deliveries: {len(clean_df):,}")

        # Clean up temp dir
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()

        # Run vectorized enrichment script to keep Hawk-Eye physics updated
        try:
            import enrich_dataset_values
            enrich_dataset_values.clean_match_dataset()
            enrich_dataset_values.simulate_missing_hawkeye_telemetry()
        except Exception as e:
            logging.warning(f"Enrichment post-step warning: {e}")

        return True
    except Exception as e:
        logging.error(f"Error extracting and merging Cricsheet match files: {e}")
        return False


def run_updater_pipeline():
    """Main updater pipeline."""
    print("=========================================================")
    print(" 🚀 AUTOMATED IPL CRICKET DATA SCRAPER & API UPDATER ")
    print("=========================================================")
    success = download_latest_cricsheet_data()
    if success:
        extract_and_merge_cricsheet_matches()
        print("🎉 Dataset updater complete!")
    else:
        print("⚠️ Failed to update live data package.")


if __name__ == "__main__":
    run_updater_pipeline()
