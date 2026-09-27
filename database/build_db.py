"""Script for a new database, generated from big 5 league event data."""
# 1. Environment & Path Setup
import os
import sys
import warnings

# Add the project root directory to sys.path so 'pipeline' is importable
sys.path.append(os.path.abspath('..'))

import numpy as np  # noqa: F401
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

# Suppress StatsBomb's NoAuthWarning specifically
warnings.filterwarnings(
    "ignore", message=".*credentials were not supplied.*"
)

# =====================================================================
# CONFIGURATION
# =====================================================================
COMP_IDS = [11, 7, 2, 12]
SEASON_ID = 27

# =====================================================================
# MAIN PIPELINE FUNCTIONS
# =====================================================================
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
    # print(f'Found {len(teams_df)} teams')
    # print()

    match_team_pairs = []

    for row in teams_df.itertuples(index=False):
        team_id = row.team_id
        competition_id = row.competition_id

        matches = get_team_matchids(competition_id, SEASON_ID, team_id)
        num_matches = len(matches)
        # print(f'Team {team_id} played {num_matches} matches')

        current_matches = pd.DataFrame({'match_id': matches})
        current_matches['team_id'] = team_id

        match_team_pairs.append([current_matches, num_matches])

    # Concatenate all individual DataFrames into one complete DataFrame
    match_team_df = pd.concat([item[0] for item in match_team_pairs], ignore_index=True)

    return match_team_df

def get_match_events(team_id, match_id):
    # print(f'Proccessing {match_id} for team {team_id}')

    df = get_events_from_timeline(team_id, match_id)
    # print('1) Added teamsheet, mandown, match_time and match_seconds columns')

    df = spatial_unpack(df)
    # print('2) Unpacked location into x and y columns')

    df = get_complete_carries(df)
    # print('3.1) Unpacked carry_end_location into end_x and end_y columns')
    # print('3.2) Added carry_distance column, Complete Carry rows with carry_end_matchseconds and total_carries columns')

    df = get_carry_outcome(df)
    # print('4) Added carry_outcome column to complete carry events')

    # print(f'Finished processing {match_id} for team {team_id}')

    return df
