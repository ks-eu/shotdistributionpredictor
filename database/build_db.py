"""Script for a new database, generated from big 5 league event data."""
# ENVIRONMENT SETUP
import os
import sys
import warnings
from datetime import datetime

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
import pandas as pd
from statsbombpy import sb  # noqa: F401

from pipeline import (
    get_carry_outcome,
    get_complete_carries,
    get_events_from_timeline,
    get_team_matchids,
    get_teams,
    spatial_unpack,
)

# CONFIGURATION
COMP_IDS = [11, 7, 2, 12]
SEASON_ID = 27
DB_PATH = 'data/events.db'
THREAD_COUNT = 6

# MAIN PIPELINE METHODS/FUNCTIONS
def team_match_pairs():
    """Return dataframe of team_match pairs."""
    team_comp_dfs = [
        pd.DataFrame({
            'team_id': get_teams(comp_id, SEASON_ID)['home_team_id'],
            'competition_id': comp_id
        })
        for comp_id in COMP_IDS
    ]

    teams_df = pd.concat(team_comp_dfs, ignore_index=True)
    print(f'Found {len(teams_df)} teams')
    print()

    match_team_pairs = []

    for row in teams_df.itertuples(index=False):
        team_id = row.team_id
        competition_id = row.competition_id

        matches = get_team_matchids(competition_id, SEASON_ID, team_id)
        num_matches = len(matches)
        print(f'Team {team_id} played {num_matches} matches')

        current_matches = pd.DataFrame({'match_id': matches})
        current_matches['team_id'] = team_id

        match_team_pairs.append([current_matches, num_matches])

    # Concatenate all individual DataFrames into one complete DataFrame
    match_team_df = pd.concat([item[0] for item in match_team_pairs], ignore_index=True)
    match_team_df = match_team_df.reset_index(drop=True)

    return match_team_df


def get_match_events(team_id, match_id):
    """Return processed event dataframe for a given match and team.
    
    Arguments:
    team_id: StatsBomb Team ID
    match_id: StatsBomb Match ID

    """
    print(f'  Proccessing {match_id} for team {team_id}:')

    df = get_events_from_timeline(team_id, match_id)
    print('    1) Added teamsheet, mandown, match_time and match_seconds columns')

    df = spatial_unpack(df)
    print('    2) Unpacked location into x and y columns')

    df = get_complete_carries(df)
    print('    3.1) Unpacked carry_end_location into end_x and end_y columns')
    print('    3.2) Added carry_distance column, Complete Carry rows with carry_end_matchseconds and total_carries columns')

    df = get_carry_outcome(df)
    print('    4) Added carry_outcome column to complete carry events')

    print(f'  Finished processing {match_id} for team {team_id}')
    print()
    return df


# DATABASE BUILDING METHODS/FUNCTIONS
def database_init():
    """Initialise duckdb database and change existing database into a backup."""
    dir_name, file_name = os.path.split(DB_PATH)
    print(f'Checking for database in path: {DB_PATH}')
    if os.path.exists(DB_PATH):
        print('Found existing database, creating backup...')
        stem, ext = os.path.splitext(file_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(dir_name, f'{stem}_{timestamp}{ext}.bak')

        os.replace(DB_PATH, backup_path)
        print(f'Removed database, backup at: {backup_path}')
    else:
        print('No existing database found')

    con = duckdb.connect(DB_PATH)
    print(f'Created new database at: {DB_PATH}')
    con.execute(f'PRAGMA threads = {THREAD_COUNT}')
    con.execute('PRAGMA preserve_insertion_order = false')

    return con


def database_build(team_match_ids, db_con):
    skipped_team_matches = []
    iter_df = team_match_ids.copy()
    batch_len = len(team_match_ids)
    print(f'Found {batch_len} team-match pairs to process')
    print()
    for row in iter_df.itertuples():
        print(f'Processing Batch {row.Index+1}/{batch_len}:')
        team_id = row.team_id
        match_id = row.match_id

        try:
            current_df = get_match_events(team_id, match_id)
            if current_df.empty:
                print(f'  Event Dataframe empty for: Team {team_id}, Match {match_id}')
                print('  Moving to next team-match pair')
                print()

            db_con.execute('CREATE TABLE IF NOT EXISTS events AS SELECT * FROM current_df WHERE 1=0;')

            db_cols = {
                row[0] for row in db_con.execute('DESCRIBE events;').fetchall()
            }

            for col in current_df.columns:
                if col not in db_cols:
                    db_con.execute(f'ALTER TABLE events ADD COLUMN "{col}" VARCHAR;')

            updated_db_cols = {
                row[0] for row in db_con.execute("DESCRIBE events;").fetchall()
            }

            for col in updated_db_cols:
                if col not in current_df.columns:
                    current_df[col] = np.nan

            db_con.execute('INSERT INTO events BY NAME SELECT * FROM current_df;')

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

# MAIN
def main():
    print('build_db: Create duckdb database for processed match event data')
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
        db_con = database_init()
    except Exception as e:
        print(f'Failed initialising database: Error {str(e)}')
        print('Ending Program')
        sys.exit(1)

    try:
        skipped_batches = database_build(team_match_ids, db_con)

        print("Skipped Records Audit")
        if not skipped_batches.empty:
            print(skipped_batches)
        else:
            print("All matches processed successfully with zero errors!")
    finally:
        print()
        db_con.close()
        print(f"Database has been built at {DB_PATH}")

if __name__ == "__main__":
    main()
