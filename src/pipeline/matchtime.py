"""Use period, timestamp columns to get a column of continuous pd.Timedelta timestamps for each event."""

import numpy as np  # noqa: F401
import pandas as pd
from statsbombpy import sb  # noqa: F401


def get_match_time(event_df):
    """Attaches a cumulative timestamp to every event in the given dataframe (must be from sb.events).

    Arguments:
    event_df: StatsBomb events type dataframe

    """
    # periods 1,2 are the two main halves of a game
    # periods 3,4 are the two halves of extra time
    # period 5 is for penalty shootouts

    # need to throw interrupt if we have more than 1 team in the data set
    df = event_df.copy()
    df['timestamp'] = pd.to_timedelta(df['timestamp'])

    halfend = df[(df['type'].isin(['Half End']))].sort_values(by = ['period']).reset_index(drop = True)
    # display(halfend.dropna(axis = 1, how = "all"))

    halfend['period_offset'] = halfend['timestamp'].cumsum()
    # display(halfend['period_offset'])

    halfend['period_offset'] = halfend['period_offset'].shift(periods = 1, fill_value = pd.Timedelta(0))
    # display(halfend['period_offset'])

    offset_dict = halfend.set_index('period')['period_offset'].to_dict()
    # print(offset_dict)

    df['period_offset'] = df['period'].map(offset_dict)
    df['match_time'] = df['timestamp'] + df['period_offset']
    return df
