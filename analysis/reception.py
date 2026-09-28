"""Get all reception events with locations from a player-match event dataframe."""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import duckdb
import numpy as np  # noqa: F401
import pandas as pd  # noqa: F401

DB_PATH = 'data/events.db'
KEY_COLUMNS = ['player_id',
               'match_id',
               'team_id',
               'player',
               'team',
               'position',
               'type',
               'match_seconds',
               'teamsheet',
               'mandown',
               'location',
               'x',
               'y',
               'play_pattern'
]
RECEPTION_TYPES = ['Ball Receipt*',
                   'Ball Recovery',
                   'Duel',
                   '50/50',
                   'Interception',
                   'Pass',
                   'Shot']

TYPE_OUTCOMES = {
    'duel_outcome' : 'Won',
    'interception_outcome' : 'Won',
    'pass_type' : 'Recovery',
    'shot_type' : 'Recovery'
}
