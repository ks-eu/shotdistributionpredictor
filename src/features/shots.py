"""Shot Usage metrics derived from StatsBomb event data - deprecated for now."""

import numpy as np
import pandas as pd

from src.pipeline.lpevents import get_uniquelineups


def get_playerusage(shotevents_df, player_id, player_name):
    """Return a list of shot stats, including player usage, and associated dataframes for a given player over a season.

    Arguments:
    shotevents_df: Dataframe of shot events with teamsheets attached for a given team over a season.
    player_id: StatsBomb player ID
    player_name: StatsBomb player name

    Output:
    5 element list - [player_shots, team_shots, player_usage, team_shots_df, player_shots_df]

    player_shots: Number of shots taken by the player over the season.
    team_shots: Number of shots taken by the team over the season when the player was on the field
    player_usage: Percentage of shots taken by the player over the season when the player was on the field.
    team_shots_df: Dataframe of all shots taken by the team over the season when the player was on the field.
    player_shots_df: Dataframe of all shots taken by the player over the season.

    Note - The returned dataframes are filtered to only include events where the team was playing with 11 players on the field.
           Will be replaced by two functions that return the each dataframe; this is a temporary solution to get the player usage metric.

    """
    # proccessedshots_df is a list of tuples with a dataframe of shot events linked to a unique team sheet
    # with the corresponding teamsheet as a frozenset
    processedshots_df = get_uniquelineups(shotevents_df)

    # filter list of tuples via the frozenset to only get dataframes where the player is found in the teamsheet
    sublist = [
        (df, f_set) for df, f_set in processedshots_df
        if (str(int(player_id)), player_name) in f_set
    ]
    # numpy array and pandas dataframe manipulation to get dataframes of all shot events with player on the field
    # and shots taken by the player, filtering out any events where the team was playing with fewer than 11 players
    subarray = np.array(sublist, dtype = object)
    new_df = pd.concat(list(subarray[:, 0]))
    new_df = new_df[(~new_df['mandown'])]
    player_df = new_df[(new_df['player_id'] == player_id)]

    return [len(player_df), len(new_df), (100*(len(player_df)/len(new_df))), new_df, player_df]
