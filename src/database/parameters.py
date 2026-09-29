"""Query Parameters.

This is deprecated
"""


KEY_RECEPTION_COLUMNS = ['player_id',
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
]

RECEPTION_TYPES = ['Ball Receipt*',
                   'Ball Recovery'
]

RECEPTION_TYPE_OUTCOMES = [
    ('Duel','duel_outcome','Won'),
    ('Interception', 'interception_outcome','Won'),
    ('Pass', 'pass_type', 'Recovery'),
    ('Shot', 'shot_type', 'Recovery')
]

KEY_RELEASE_COLUMNS = ['player_id',
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
                'carry_end_location',
                'end_x',
                'end_y'
]

RELEASE_TYPES = ['Pass',
                 'Shot']

RELEASE_TYPE_OUTCOMES = [('Complete Carry', 'carry_end_outcome', 'Other')]

