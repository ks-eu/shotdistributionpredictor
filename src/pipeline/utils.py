"""Utilities for fetching data from StatsBomb API."""

import numpy as np
import pandas as pd
from statsbombpy import sb


def get_teams(comp_id, season_id):
    """Return dataframe of teams for given competition and season.
    
    Arguments:
    comp_id: StatsBomb competition ID
    season_id: StatsBomb season ID

    """
    season_matches = sb.matches(competition_id=comp_id,
                                season_id=season_id)

    return (season_matches[['home_team_id', 'home_team']]
            .copy()
            .drop_duplicates()
            .sort_values(by=['home_team_id'])
            .reset_index(drop=True))


def get_team_matchids(comp_id, season_id, team_id):
    """Return list of match IDs for a given team in given competition and season.
    
    Arguments:
    comp_id: StatsBomb competition ID
    season_id: StatsBomb season ID
    team_id: StatsBomb team ID

    """
    season_matches = sb.matches(competition_id=comp_id,
                                season_id=season_id)
    season_matches["match_date"] = pd.to_datetime(season_matches["match_date"])
    team_matches = (season_matches[(season_matches['home_team_id']
                                    == team_id)
                                   | (season_matches['away_team_id']
                                      == team_id)]
                    .reset_index(drop=True))
    team_matches = team_matches.sort_values(by = "match_date").reset_index(drop=True)
    team_matches["matchweek"] = range(1, len(team_matches)+1)
    return team_matches[["match_id", "matchweek"]]


def spatial_unpack(event_df, targetcolumn = 'location', x_name = 'x', y_name = 'y'):
    """Return dataframe with spatial data unpacked as 2 columns.
    
    Arguments:
    event_df: StatsBomb Event dataframe
    targetcolumn: Name of the column with spatial coordinates that need unpacking
    x_name: Name of the new x coordinate column
    y_name: Name of the new y coordiante_column
    
    """
    df = event_df.copy()

    # 1. Replace missing/NaN entries with a [NaN, NaN] list fallback
    has_loc = df[targetcolumn].notna()
    df[targetcolumn] = np.where(
        has_loc, df[targetcolumn], pd.Series([[np.nan, np.nan]] * len(df), index=df.index)
    )

    df[[x_name, y_name]] = pd.DataFrame(df[targetcolumn].tolist(), index=df.index)
    return df


# might need to change how this works (either force column to be string or change to a dict comprehension)
def get_ff_outcome(event_df):
    """Add ff_outcome column to an event dataframe.
    
    Arguments:
    event_df: StatsBomb event dataframe
    
    """ 
    df = event_df.copy()
    ff_value = df["50_50"].str.extract(
        r"'name':\s*([^}]+)"
    )
    df['ff_outcome'] = ff_value
    return df

def team_match_pairs(comp_ids : list, season_id : int):
    """Return dataframe of team_match pairs."""
    team_comp_dfs = [
        pd.DataFrame({
            'team_id': get_teams(comp_id, season_id=season_id)['home_team_id'],
            'competition_id': comp_id
        })
        for comp_id in comp_ids
    ]

    teams_df = pd.concat(team_comp_dfs, ignore_index=True)
    print(f'Found {len(teams_df)} teams')
    print()

    match_team_pairs = []

    for row in teams_df.itertuples(index=False):
        team_id = row.team_id
        competition_id = row.competition_id

        current_matches = get_team_matchids(competition_id, season_id, team_id)
        num_matches = len(current_matches)
        print(f'Team {team_id} played {num_matches} matches')
        current_matches['team_id'] = team_id

        match_team_pairs.append([current_matches, num_matches])

    # Concatenate all individual DataFrames into one complete DataFrame
    match_team_df = pd.concat([item[0] for item in match_team_pairs], ignore_index=True)
    match_team_df = match_team_df.reset_index(drop=True)

    return match_team_df
