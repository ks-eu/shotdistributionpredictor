"""Get Pandas Dataframes from Queries."""
import os
import sys  # noqa F401

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "events.db")

import numpy as np  # noqa F401
import pandas as pd  # noqa F401

import duckdb

from src.database.queries import RECEPTION_QUERY, RELEASE_QUERY
from src.pipeline import get_ff_outcome


def event_connection(read_only: bool = True, threads : int = 1):
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database file not found at: {DB_PATH}. "
            "Please ensure data/events.db exists."
        )
    con = duckdb.connect(database=DB_PATH, read_only=read_only)
    con.execute(f'PRAGMA threads = {threads}')
    return con

def _mt_query(team_id : int, match_id : int):
    return f" AND match_id = '{match_id}' AND team_id = '{team_id}' ORDER BY match_seconds ASC;"

def get_matchevent_receptions(team_id : int, match_id : int, threads : int = 1):
    query = RECEPTION_QUERY + _mt_query(team_id, match_id)
    con = event_connection(threads=threads)
    df = con.execute(query).df()
    df = get_ff_outcome(df)
    df = df[(df['type'] != '50/50') | (df['ff_outcome'] == 'Won')]
    con.close()
    return df

def get_matchevent_releases(team_id : int, match_id : int, threads : int = 1):
    query = RELEASE_QUERY + _mt_query(team_id, match_id)
    con = event_connection(threads)
    df = con.execute(query).df()
    con.close()
    return df
