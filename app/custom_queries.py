
BEST_PLAYOFF_RECORD_SQL = """
SELECT  *
FROM    club_records
WHERE   club_pk = :clubpk
AND     user_pk = :userpk
AND     last_playoff_series_pk IN (
    SELECT  pk
    FROM    playoff_series
    WHERE   user_pk = :userpk
    AND     (top_seed_pk = :clubpk OR low_seed_pk = :clubpk)
    AND     round_n = (
        SELECT  Max(round_n)
        FROM    playoff_series
        WHERE   user_pk = :userpk
        AND     (top_seed_pk = :clubpk OR low_seed_pk = :clubpk)
    )
)
ORDER BY season_n
"""

BEST_REGULAR_RECORD_SQL = """
SELECT  *
FROM    club_records
WHERE   user_pk = :userpk
AND     club_pk = :clubpk
AND     regular_season_position_n = (
    SELECT  Min(regular_season_position_n)
    FROM    club_records
    WHERE   user_pk = :userpk
    AND     club_pk = :clubpk
)
ORDER BY season_n
"""

CLUB_PLAYERS_SQL = """
SELECT pk_n, first_name_c, second_name_c, last_name_c, technique_n, age_n, club_pk, endurance_n, current_stamina_n
FROM  players
WHERE user_pk = {0:d}
AND   club_pk = {1:d}
AND   is_active = 1
AND   is_drafted = 1
"""

CLUB_RECORDS_SQL = """
SELECT  *
FROM    club_records
WHERE   user_pk = :userpk
AND     club_pk = :clubpk
ORDER BY season_n DESC
"""

CURRENT_MATCH_SQL = """
SELECT match_pk_n, (
    SELECT club_name_c
    FROM   clubs
    WHERE  club_id_n = matches.home_team_pk
), (
    SELECT club_name_c
    FROM   clubs
    WHERE  club_id_n = matches.away_team_pk
), home_team_pk, away_team_pk
FROM matches
WHERE season_n = {1:d}
AND   day_n = {2:d}
AND   (home_team_pk = {0:d} OR away_team_pk = {0:d})
AND   user_pk = {3:d}
AND   status_en = 'planned'
"""

DAY_RESULTS_SQL = """
SELECT match_pk_n, (
    SELECT club_name_c
    FROM   clubs
    WHERE  clubs.club_id_n = matches.home_team_pk
), (
    SELECT club_name_c
    FROM   clubs
    WHERE  clubs.club_id_n = matches.away_team_pk
), (
    SELECT first_name_c || ' ' || last_name_c
    FROM   players
    WHERE  players.pk_n = matches.home_player_pk
), (
    SELECT first_name_c || ' ' || last_name_c
    FROM   players
    WHERE  players.pk_n = matches.away_player_pk
), (
    SELECT (technique_n + endurance_n) / 2
    FROM   players
    WHERE  players.pk_n = matches.home_player_pk
), (
    SELECT (technique_n + endurance_n) / 2
    FROM   players
    WHERE  players.pk_n = matches.away_player_pk
), full_score_c, home_team_pk, away_team_pk
FROM matches
WHERE user_pk = {0:d}
AND season_n = {1:d}
AND day_n = {2:d}
AND status_en = 'finished'
"""

FINAL_PLAYOFF_SERIES_FOR_CLUB_SQL = """
SELECT *
FROM    playoff_series
WHERE   user_pk = :userpk
AND     season_n = :season
AND     (
    top_seed_pk = :club_pk OR low_seed_pk = :club_pk
)
AND     round_n = (
    SELECT  Max(round_n)
    FROM    playoff_series
    WHERE   user_pk = :userpk
    AND     season_n = :season
    AND     (
        top_seed_pk = :club_pk OR low_seed_pk = :club_pk
    )
)
"""

GLOBAL_USER_RATING_SQL = """
SELECT users_outer.pk, users_outer.username, Round(
(
    SELECT Avg(last_round * 25 * (matches_won * 2 + 1))
    FROM (
        SELECT Sum(
            CASE
            WHEN matches.home_team_pk = users_outer.managed_club_pk AND matches.home_sets_n > matches.away_sets_n
            THEN 1
            WHEN matches.away_team_pk = users_outer.managed_club_pk AND matches.away_sets_n > matches.home_sets_n
            THEN 1
            ELSE 0
            END
        ) AS matches_won, club_records.season_n, (
            SELECT round_n
            FROM playoff_series
            WHERE playoff_series.pk = club_records.last_playoff_series_pk
        ) AS last_round
        FROM club_records, matches
        WHERE club_records.user_pk = users_outer.pk
        AND club_records.club_pk = users_outer.managed_club_pk
        AND matches.playoff_series_pk = club_records.last_playoff_series_pk
        AND matches.status_en = 'finished'
        GROUP BY club_records.last_playoff_series_pk
    )
) + (
    SELECT Avg(club_records.regular_season_points_n)
    FROM club_records
    WHERE club_records.user_pk = users_outer.pk
    AND club_records.club_pk = users_outer.managed_club_pk
) * :regular_points_factor, :precision
) AS rating_points
FROM users AS users_outer
WHERE rating_points NOT NULL
ORDER BY rating_points DESC
"""

MAX_DAY_IN_SEASON_SQL = """
SELECT Max(day_n)
FROM   matches
WHERE  user_pk = {0:d}
AND    season_n = {1:d}
"""

MAX_PLAYOFF_ROUND_SQL = """
SELECT Max(round_n) AS max_round
FROM   playoff_series
WHERE  user_pk = {user_pk}
AND    season_n = {season}
"""

RECENT_PLAYER_MATCHES_SQL = """
SELECT   match_pk_n, (
    SELECT club_name_c
    FROM   clubs
    WHERE  clubs.club_id_n = matches.home_team_pk
), (
    SELECT club_name_c
    FROM   clubs
    WHERE  clubs.club_id_n = matches.away_team_pk
), (
    SELECT players.first_name_c || ' ' || players.second_name_c || ' ' || players.last_name_c
    FROM   players
    WHERE  players.pk_n = matches.home_player_pk
), (
    SELECT players.first_name_c || ' ' || players.second_name_c || ' ' || players.last_name_c
    FROM   players
    WHERE  players.pk_n = matches.away_player_pk
), full_score_c
FROM     matches
WHERE    (home_player_pk = {0:d} OR away_player_pk = {0:d})
AND      season_n = {1:d}
AND      status_en = 'finished'
ORDER BY day_n DESC
LIMIT    {2:d}
"""

SERIES_IN_ONE_ROUND_IN_ONE_DIVISION_SQL = """
SELECT *
FROM playoff_series
WHERE user_pk = :user
AND season_n = :season
AND round_n = :rnd
AND top_seed_pk IN (
    SELECT club_id_n
    FROM clubs
    WHERE division_n = :division
)
ORDER BY pk
"""

STANDINGS_SQL = """
SELECT club_id_n, club_name_c, (
    SELECT Sum(
        CASE WHEN home_team_pk = clubs.club_id_n
        THEN home_sets_n
        ELSE 0 END +
        CASE WHEN away_team_pk = clubs.club_id_n
        THEN away_sets_n
        ELSE 0 END
    )
    FROM  matches
    WHERE season_n = {0:d}
    AND   user_pk = {1:d}
    AND   status_en = 'finished'
    AND   playoff_series_pk IS NULL
) AS sets, (
    SELECT Sum(
        CASE WHEN home_team_pk = clubs.club_id_n
        THEN home_games_n
        ELSE 0 END +
        CASE WHEN away_team_pk = clubs.club_id_n
        THEN away_games_n
        ELSE 0 END
    )
    FROM  matches
    WHERE season_n = {0:d}
    AND   user_pk = {1:d}
    AND   status_en = 'finished'
    AND   playoff_series_pk IS NULL
) AS games, (
    SELECT Count(*)
    FROM   matches
    WHERE  (home_team_pk = clubs.club_id_n OR away_team_pk = clubs.club_id_n)
    AND    status_en = 'finished'
    AND    season_n = {0:d}
    AND    user_pk = {1:d}
    AND    playoff_series_pk IS NULL
) AS played
FROM clubs
ORDER BY sets DESC, games DESC
"""

STANDINGS_FOR_DIVISION_SQL = STANDINGS_SQL[0:-31] + "WHERE division_n = {2:d}\n" + STANDINGS_SQL[-31:]
