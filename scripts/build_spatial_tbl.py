"""Script for a new database, generated from big 5 league event data."""
# ENVIRONMENT SETUP
import os
import sys
import warnings

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

warnings.filterwarnings(
    "ignore", message=".*credentials were not supplied.*"
)

# MODULE IMPORTS
import duckdb
import numpy as np
import pandas as pd  # noqa: F401

from src.features import op_pm_avg_locations
from src.pipeline import team_match_pairs

# CONFIG
COMP_IDS = [11, 7, 2, 12]
SEASON_ID = 27
DB_PATH = 'data/events.db'
THREAD_COUNT = 6

def database_check():
    """Check if duckdb database exists in filepath."""
    print(f'Checking for database in path: {DB_PATH}')
    if os.path.exists(DB_PATH):
        print('Found existing database')
        return False
    else:
        print('No existing database found')
        return True

def optbl_clear():
    """Clear the open play table if it exists in the database."""
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS opspatial;")
    con.close()

def optbl_build(team_match_ids):
    skipped_team_matches = []
    iter_df = team_match_ids.copy()
    batch_len = len(team_match_ids)
    print(f'Found {batch_len} team-match pairs to process')
    print()

    con = duckdb.connect(DB_PATH)
    for row in iter_df.itertuples():
        print(f'Processing Batch {row.Index+1}/{batch_len}:')
        team_id = row.team_id
        match_id = row.match_id

        try:
            current_df = op_pm_avg_locations(team_id, match_id, threads = THREAD_COUNT)
            if current_df.empty:
                print(f'  Player Dataframe empty for: Team {team_id}, Match {match_id}')
                print('  Moving to next team-match pair')
                print()

            con.execute('CREATE TABLE IF NOT EXISTS opspatial AS SELECT * FROM current_df WHERE 1=0;')

            db_cols = {
                row[0] for row in con.execute('DESCRIBE opspatial;').fetchall()
            }

            for col in current_df.columns:
                if col not in db_cols:
                    con.execute(f'ALTER TABLE opspatial ADD COLUMN "{col}" VARCHAR;')

            updated_db_cols = {
                row[0] for row in con.execute("DESCRIBE opspatial;").fetchall()
            }

            for col in updated_db_cols:
                if col not in current_df.columns:
                    current_df[col] = np.nan

            con.execute('INSERT INTO opspatial BY NAME SELECT * FROM current_df;')

            print(f'  Inserted processed event data for: Team {team_id}, Match {match_id}')
            print()

        except Exception as e:
            error_msg = f"  Failed Match: {match_id}, Team: {team_id}. Error: {str(e)}"
            print(f"{error_msg}")
            skipped_team_matches.append(
                {"team_id": team_id, "match_id": match_id, "error": str(e)}
            )
            print('  Moving to next team-match pair')
            print()
            continue
    print("Ingestion Summary:")
    print(
        f"Total Attempted: {len(iter_df)} | Total Skipped: {len(skipped_team_matches)}"
    )
    print()
    return skipped_team_matches

def main():
    print(f"build_spatial_tbl: Create new table for database at {DB_PATH} for average coordinates in open play for football players.")
    print(f'Competition IDs: {COMP_IDS}, Season ID: {SEASON_ID}')
    print(f'Number of threads to be used: {THREAD_COUNT}')
    print(f'Database file path {DB_PATH}, NOTE: This is a local path, relative to the parent directory of this program')
    print()
    cont = False
    for x in range(1,6):
        answer = input('Do you want to build the database? [y/n]')
        if answer == 'y' or answer == 'yes' or answer == 'Y' or answer == 'Yes':
            cont = True
            break
        elif answer == 'n' or answer == 'no' or answer == 'N' or answer == 'No':
            break
        else:
            print(f'Invalid input, try again ({x} tries left)')

    if not cont:
        print("Ok! Ending Program")
        sys.exit(0)

    print("Ok! Starting Database Build")
    print()

    try:
        team_match_ids = team_match_pairs()
    except Exception as e:
        print(f'Failed retrieving team-match pairs: Error {str(e)}')
        print('Ending Program')
        sys.exit(1)

    try:
        db_check = database_check()
        if not db_check:
            print('Ending Program')
    except Exception as e:
        print(f"Could not check if database exists at {DB_PATH}: Error {str(e)}")
        print('Ending Program')
        sys.exit(1)

    try:
        print("Clearing table \"opspatial\" if it exists")
        optbl_clear()
    except Exception as e:
        print(f"Failed in clearing table if it exists: Error {str(e)}")
        print('Ending Program')
        sys.exit(1)

    skipped_batches = optbl_build(team_match_ids)
    print(f"Database has been built at {DB_PATH}")

if __name__ == "__main__":
    main()