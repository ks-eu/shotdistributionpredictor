-- primary table
CREATE TEMP TABLE pass_distance AS SELECT
    player_id,
    first(player) AS player,
    avg(pass_end_x - x) AS average_pass_x_displacement,
    avg(abs(pass_end_y - y)) AS average_pass_norm_y_displacement,
    count(*) AS pass_total
FROM events
WHERE
    (
        (type = 'Pass') AND
        (position <> 'Goalkeeper')
    ) 
    AND (mandown = False)
    AND
    (
        (play_pattern = 'Regular Play') OR
        (play_pattern = 'From Keeper') OR
        (play_pattern = 'From Counter') OR
        (play_pattern = 'From Throw In')
    )
    AND (matchweek >= $1 AND matchweek <= $2)
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE carry_distance AS SELECT
    player_id,
    first(player) AS player,
    avg(end_x - x) AS average_carry_x_displacement,
    avg(abs(end_y - y)) AS average_carry_norm_y_displacement,
    count(*) AS carry_total
FROM events
WHERE
    (
        (type = 'Complete Carry')
    ) 
    AND (mandown = False)
    AND
    (
        (play_pattern = 'Regular Play') OR
        (play_pattern = 'From Keeper') OR
        (play_pattern = 'From Counter') OR
        (play_pattern = 'From Throw In')
    )
    AND (matchweek >= $1 AND matchweek <= $2)
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE player_rel AS SELECT
    player_id,
    match_id,
    team_id,
    player,
    position,
    type,
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
        END AS y
FROM
    events
WHERE
    (
        (type = 'Pass') OR
        (type = 'Shot') OR
        ((type = 'Complete Carry') AND (carry_end_outcome = 'Other'))
    ) 
    AND (mandown = False)
    AND
    (
        (play_pattern = 'Regular Play') OR
        (play_pattern = 'From Keeper') OR
        (play_pattern = 'From Counter') OR
        (play_pattern = 'From Throw In')
    )
    AND (matchweek >= $1 AND matchweek <= $2);

-- secondary table from "player_rel"
CREATE TEMP TABLE player_rel_avg AS SELECT
    player_id,
    first(player) AS player,
    avg(x) AS avg_rel_x,
    avg(y) AS avg_rel_y,
    avg(40 - ABS(y - 40)) AS avg_normrel_y,
    count(*) AS rel_total
FROM player_rel
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE player_rec AS SELECT
    player_id,
    match_id,
    team_id,
    player,
    position,
    type,
    match_seconds,
    teamsheet,
    mandown,
    play_pattern,
    x,
    y,
FROM
    events
WHERE 
    (
        (type = 'Ball Receipt*') OR
        (type = 'Ball Recovery') OR
        ((type = '50/50') AND ("50_50".outcome.name = 'Won')) OR
        ((type = 'Duel') AND (duel_outcome = 'Won')) OR
        ((type = 'Interception') AND (interception_outcome = 'Won')) OR
        ((type = 'Pass') AND (pass_type = 'Recovery')) OR
        ((type = 'Shot') AND (shot_type = 'Recovery'))
    )
    AND (mandown = False)
    AND
    (
        (play_pattern = 'Regular Play') OR
        (play_pattern = 'From Keeper') OR
        (play_pattern = 'From Counter') OR
        (play_pattern = 'From Throw In')
    )
    AND (matchweek >= $1 AND matchweek <= $2);

-- secondary table from "player_rec"
CREATE TEMP TABLE player_rec_avg AS SELECT
    player_id,
    first(player) AS player,
    avg(x) AS avg_rec_x,
    avg(y) AS avg_rec_y,
    avg(40 - ABS(y - 40)) AS avg_normrec_y,
    count(*) AS rec_total
FROM player_rec
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE key_pass AS SELECT
    player_id,
    first(player) AS player,
    count(*) AS key_pass_total
FROM
    events
WHERE
    (
        (type = 'Pass') AND
        (pass_shot_assist)
    )
    AND (matchweek >= $1 AND matchweek <= $2)
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE shot_count AS SELECT
    player_id,
    first(player) AS player,
    count(*) AS shot_total
FROM events
WHERE type = 'Shot' AND (matchweek >= $1 AND matchweek <= $2)
GROUP BY player_id;

-- primary table
CREATE TEMP TABLE reception AS
    SELECT
        player_id,
        match_id,
        team_id,
        player,
        type,
        match_seconds,
        play_pattern,
        x,
        y,
    FROM
        events
    WHERE
        (
            (type = 'Ball Receipt*') OR
            (type = 'Ball Recovery') OR
            ((type = '50/50') AND ("50_50".outcome.name = 'Won')) OR
            ((type = 'Duel') AND (duel_outcome = 'Won')) OR
            ((type = 'Interception') AND (interception_outcome = 'Won'))
        )
        AND (matchweek >= $1 AND matchweek <= $2)
    ORDER BY
        match_id, team_id, match_seconds;

-- primary table
CREATE TEMP TABLE outcome AS
    SELECT
        player_id,
        match_id,
        team_id,
        type,
        match_seconds
    FROM
        events
    WHERE
        (
            (type = 'Pass') OR
            (type = 'Shot') OR
            (type = 'Complete Carry')
        )
        AND (matchweek >= $1 AND matchweek <= $2)
    ORDER BY
        match_id, team_id, match_seconds;

-- secondary table from "reception" and "outcome"
CREATE TEMP TABLE reception_outcomes AS
SELECT
    l.player_id as player_id,
    l.match_id as match_id,
    l.team_id as team_id,
    l.player as player,
    l.type as type,
    l.match_seconds as match_seconds,
    l.play_pattern as play_pattern,
    l.x as x,
    l.y as y,
    r.type as reception_outcome
FROM reception l LEFT JOIN outcome r ON
    l.player_id = r.player_id AND
    l.match_id = r.match_id AND
    l.team_id = r.team_id AND
    l.match_seconds = r.match_seconds;

-- tertiary table from "reception_outcomes"
CREATE TEMP TABLE outcome_pass_count AS
SELECT
    player_id,
    first(player) as player,
    count(*) as outcome_count
FROM reception_outcomes
WHERE reception_outcome = 'Pass'
GROUP BY player_id;

-- tertiary table from "reception_outcomes"
CREATE TEMP TABLE outcome_carry_count AS
SELECT
    player_id,
    first(player) as player,
    count(*) as outcome_count
FROM reception_outcomes
WHERE reception_outcome = 'Complete Carry'
GROUP BY player_id;

-- tertiary table from "reception_outcomes"
CREATE TEMP TABLE outcome_shot_count AS
SELECT
    player_id,
    first(player) as player,
    count(*) as outcome_count
FROM reception_outcomes
WHERE reception_outcome = 'Shot'
GROUP BY player_id;

-- returned table
SELECT
    l.player_id AS player_id,
    l.player AS player,
    l.average_pass_x_displacement AS average_pass_x_displacement,
    l.average_pass_norm_y_displacement AS average_pass_norm_y_displacement,
    l.pass_total AS pass_total,
    r.average_carry_x_displacement AS average_carry_x_displacement,
    r.average_carry_norm_y_displacement AS average_carry_norm_y_displacement,
    r.carry_total AS carry_total,
    a.avg_rel_x AS average_release_x,
    a.avg_rel_y AS average_release_y,
    a.avg_normrel_y AS average_norm_release_y,
    a.rel_total AS rel_total,
    b.avg_rec_x AS average_reception_x,
    b.avg_rec_y AS average_reception_y,
    b.avg_normrec_y AS average_norm_reception_y,
    b.rec_total AS rec_total,
    (c.key_pass_total / (c.key_pass_total + d.shot_total)) AS key_pass_shot_ratio,
    c.key_pass_total AS key_pass_total,
    d.shot_total AS shot_total,
    (oc.outcome_count/(op.outcome_count + oc.outcome_count + osh.outcome_count)) AS carry_shotpass_ratio,
    op.outcome_count AS outcome_pass_total,
    oc.outcome_count AS outcome_carry_total,
    osh.outcome_count AS outcome_shot_total
FROM pass_distance l
INNER JOIN carry_distance r ON
    l.player_id = r.player_id AND
    l.player = r.player
INNER JOIN player_rel_avg a ON
    l.player_id = a.player_id AND
    l.player = a.player
INNER JOIN player_rec_avg b ON
    l.player_id = b.player_id AND
    l.player = b.player
INNER JOIN key_pass c ON
    l.player_id = c.player_id AND
    l.player = c.player
INNER JOIN shot_count d ON
    l.player_id = d.player_id AND
    l.player = d.player
INNER JOIN outcome_pass_count op ON
    l.player_id = op.player_id AND
    l.player = op.player
INNER JOIN outcome_carry_count oc ON
    l.player_id = oc.player_id AND
    l.player = oc.player
INNER JOIN outcome_shot_count osh ON
    l.player_id = osh.player_id AND
    l.player = osh.player
WHERE
    (a.rel_total >= 50 AND
    b.rec_total >= 50);
