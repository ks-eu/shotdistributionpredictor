"""SQL Queries for the database."""

# SQL QUERY STRINGS
RECEPTION_QUERY = """
SELECT
    player_id,
    match_id,
    team_id,
    player,
    team,
    position,
    type,
    match_seconds,
    teamsheet,
    mandown,
    play_pattern,
    x,
    y,
    duel_outcome,
    interception_outcome,
    pass_type,
    shot_type,
    "50_50"
FROM
    events
WHERE 
    (
        (type = 'Ball Receipt*') OR
        (type = 'Ball Recovery') OR
        (type = '50/50') OR
        ((type = 'Duel') AND (duel_outcome = 'Won')) OR
        ((type = 'Interception') AND (interception_outcome = 'Won')) OR
        ((type = 'Pass') AND (pass_type = 'Recovery')) OR
        ((type = 'Shot') AND (shot_type = 'Recovery'))
    )
    AND (mandown = False)
"""

RELEASE_QUERY = """
SELECT
    player_id,
    match_id,
    team_id,
    player,
    team,
    position,
    CASE
        WHEN type = 'Complete Carry' THEN 'Complete Carry End'
        ELSE type
        END AS type,
    match_seconds,
    teamsheet,
    mandown,
    play_pattern,
    CASE
        WHEN type = 'Complete Carry' THEN end_x
        ELSE x
        END AS x,
    CASE
        WHEN type = 'Complete Carry' THEN end_y
        ELSE y
        END AS y,
    pass_type,
    shot_type,
    carry_end_outcome
FROM
    events
WHERE
    (
        (type = 'Pass') OR
        (type = 'Shot') OR
        ((type = 'Complete Carry') AND (carry_end_outcome = 'Other'))
    ) 
    AND (mandown = False)
"""
