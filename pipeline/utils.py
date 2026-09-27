"""Utilities for fetching data from StatsBomb API."""

import numpy as np  # noqa: F401
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
    team_matches = (season_matches[(season_matches['home_team_id']
                                    == team_id)
                                   | (season_matches['away_team_id']
                                      == team_id)]
                    .reset_index(drop=True))
    return team_matches['match_id'].to_list()


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
