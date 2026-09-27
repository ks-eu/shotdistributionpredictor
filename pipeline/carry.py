"""Concatenating carry events for a match when split by dribble events."""

import numpy as np
import pandas as pd
from statsbombpy import sb  # noqa: F401

from pipeline.utils import spatial_unpack


def union_related_events(series):
    """Take related events column for chained carry events, return union of the related events.

    Arguments:
    series: Related events column

    """
    # use set union for rapid unique combination of related event lists
    ret_set = set()
    for x in series:
        if isinstance(x, list):
            cur_set = set(x)
        elif pd.isna(x):
            cur_set = set()
        else:
            cur_set = set(x)
        ret_set = ret_set.union(cur_set)
    return list(ret_set)


def get_complete_carries(event_df):
    """Take StatsBomb match event dataframe and return rows for chained carries.
    
    Arguments:
    event_df: StatsBomb match event dataframe
    
    """
    df = event_df.copy()
    carry_events = df[df['type'] == 'Carry']

    # unpacking spatial columns, adding the match second where the carry is recorded as ending and the distance of carry
    carry_events = carry_events.sort_values(by = ['match_seconds'])
    carry_events['carry_end_seconds'] = carry_events['match_seconds'] + carry_events['duration']
    carry_events = spatial_unpack(carry_events)
    carry_events = spatial_unpack(carry_events, targetcolumn='carry_end_location', x_name='end_x', y_name = 'end_y')
    carry_events['carry_distance'] = np.sqrt(
        ((carry_events['x'] - carry_events['end_x'])**2) +
        ((carry_events['y'] - carry_events['end_y'])**2)
    )

    # applying a row shift, and calculating differences between a carry event and its successor
    next_carry_events = carry_events.shift(-1).copy()
    time_diff = next_carry_events['match_seconds'] - carry_events['carry_end_seconds']
    spatial_diff = np.sqrt(
        ((carry_events['end_x'] - next_carry_events['x'])**2) +
        ((carry_events['end_y'] - next_carry_events['y'])**2)
    )
    player_diff = (carry_events['player_id'] == next_carry_events['player_id'])

    # logic determining if carry events chain
    chain_continues = (time_diff <= 0.150) & (spatial_diff <= 0.5) & (player_diff)
    chain_starts = ~chain_continues.shift(1, fill_value=False)
    carry_events['chain_id'] = chain_starts.cumsum()

    # add a total carry column, and list aggregation rules for each column
    carry_events['total_carries'] = 1
    agg_rules = {col: 'first' for col in carry_events.columns}
    agg_rules.update({
        'end_x': 'last',
        'end_y': 'last',
        'carry_end_location': 'last',
        'carry_distance': 'sum',
        'duration': 'sum',
        'total_carries': 'sum',
        'under_pressure': lambda p: p.fillna(False).astype(bool).any(),
        'id': lambda _: np.nan,
        'index': lambda _: np.nan,
        'related_events': union_related_events,
    })

    # generate a dataframe of the complete carry events
    complete_carries = carry_events.groupby('chain_id', as_index=False).agg(agg_rules)
    complete_carries['type'] = 'Complete Carry'

    # concatenate the dataframes
    df = pd.concat([df, complete_carries], ignore_index = True)
    return df
