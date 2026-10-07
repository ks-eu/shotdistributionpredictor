"""Lineup Event Processing for StatsBomb data."""
 
import numpy as np  # noqa: F401
import pandas as pd
from statsbombpy import sb

from src.pipeline.matchtime import get_match_time


def get_teamsheet(lineup):
    """Return list representing a teamsheet.
    
    Arguments:
    lineup: Dictionary from StatsBomb event data, from the 'tactics' column of a Starting XI event.
    
    Using frozensets to represent teamsheets allows for easy and quick comparison between event points.

    """
    player_data = set()
    for player in lineup['lineup']:
        player_data.add(player['player']['id'])
    return sorted(list(player_data))


def sub_teamsheet(lineup, subin_id, subout_id):
    """Return tuple representing a teamsheet after a substitution.
    
    Arguments:
    lineup: Current teamsheet as a frozenset.
    subin_id: ID of the player coming on.
    subin_name: Name of the player coming on.
    subout_id: ID of the player going off.
    subout_name: Name of the player going off.

    """
    mut_lineup = set(lineup)
    mut_lineup.remove(int(subout_id))
    mut_lineup.add(int(subin_id))
    return sorted(list(mut_lineup))


def playeroff_teamsheet(lineup, out_id):
    """Return tuple representing a teamsheet after a player is substituted off.

    Arguments:
    lineup: Current teamsheet as a frozenset.
    out_id: ID of the player being substituted off.
    out_name: Name of the player being substituted off.

    """
    mut_lineup = set(lineup)
    mut_lineup.remove(int(out_id))
    return sorted(list(mut_lineup))


def playeron_teamsheet(lineup, on_id):
    """Return frozenset representing a teamsheet after a player is substituted on.

    Arguments:
    lineup: Current teamsheet as a frozenset.
    on_id: ID of the player being substituted on.
    on_name: Name of the player being substituted on.

    """
    mut_lineup = set(lineup)
    mut_lineup.add(int(on_id))
    return sorted(list(mut_lineup))


def mandown_teamsheet(lineup):
    """Return boolean indicating if a teamsheet has fewer than 11 players.

    Arguments:
    lineup: Teamsheet as a frozenset.

    """
    return len(lineup) < 11


# see if vectorising is an option for this function
def get_lineup_events(event_df):
    """Return dataframe, given an match event dataframe for a specific team, with teamsheet change events for that team and match.
    
    Arguments:
    event_df: StatsBomb events type dataframe
    
    """
    selected_types = ['Starting XI', 'Half End', 'Substitution',
                     'Player On', 'Player Off']
    df = event_df.copy()

    filtered_df = df[df['type'].isin(selected_types)]
    filtered_df = filtered_df.sort_values(by = ['match_time']).copy()
    filtered_df = filtered_df[ ~((filtered_df['type'] == 'Half End') &
                                (filtered_df['period'] == 1))]
    filtered_df = filtered_df.reset_index(drop = True)


    # get the starting lineup array
    starting_xi_event = filtered_df[filtered_df['type'] == 'Starting XI'].iloc[0]

    starting_xi = starting_xi_event['tactics']
    starting_ts = get_teamsheet(starting_xi)

    teamsheets = [starting_ts]
    mandown = []
    for idx, row in filtered_df.iterrows():
        event_type = row['type']
        # handling changes in teamsheets for different event types
        if event_type == 'Starting XI':
            pass

        elif event_type == 'Substitution':
            subout_id = row['player_id']
            subin_id = row['substitution_replacement_id']
            teamsheets.append(sub_teamsheet(teamsheets[idx - 1], subin_id,
                                            subout_id))

        elif event_type == 'Player Off':
            out_id = row['player_id']
            teamsheets.append(playeroff_teamsheet(teamsheets[idx - 1], out_id))

        elif event_type == 'Player On':
            on_id = row['player_id']
            teamsheets.append(playeron_teamsheet(teamsheets[idx - 1], on_id))

        elif event_type == 'Half End':
            teamsheets.append(teamsheets[idx - 1])

        # adding boolean value to mandown based on if the teamsheet has a numpy nan value
        # keeps track of when a team is playing with 10 or less players
        mandown.append(mandown_teamsheet(teamsheets[idx]))

    # adding teamsheet and "mandown" information corresponding to the lineup change events
    filtered_df['teamsheet'] = teamsheets
    filtered_df['mandown'] = mandown
    filtered_df.loc[:, 'teamsheet'] = filtered_df['teamsheet']

    columns_to_retain = ['id', 'index', 'match_id', 'team', 'team_id', 'period',
                         'timestamp', 'period_offset', 'match_time', 'type', 'teamsheet', 'mandown']

    return filtered_df[columns_to_retain].reset_index(drop=True)


def get_events_from_timeline(team_id, match_id):
    """Return dataframe of events for a given team and match attached with match time, match seconds, teamsheet and mandown information for each event.
    
    Arguments:
    team_id: StatsBomb team ID
    match_id: StatsBomb match ID

    """
    # initialise event and lineup events for the given team and match
    df = sb.events(match_id=match_id)
    df = df[df['team_id'] == team_id]
    events_df = get_match_time(df)
    events_df = events_df.sort_values(by=['match_time']).reset_index(drop=True)
    lineup_events = get_lineup_events(events_df)
    lineup_events = lineup_events[['match_time', 'teamsheet', 'mandown']]
    events_lineup_df = pd.merge_asof(events_df, lineup_events, on = 'match_time')
    events_lineup_df['match_seconds'] = events_lineup_df['match_time'].dt.total_seconds()

    return events_lineup_df
