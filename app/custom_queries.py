
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

EXISTING_FRIENDSHIP_SQL = """
SELECT  Count(*) AS number_of_existing_friendships
FROM    friendship
WHERE (
    (friend_one_pk = :u1_pk AND friend_two_pk = :u2_pk) OR 
    (friend_one_pk = :u2_pk AND friend_two_pk = :u1_pk)
)
AND     is_active = 1
"""

FRIENDS_SQL = """
SELECT *
FROM users
WHERE pk IN (
    SELECT  friend_two_pk
    FROM    friendship
    WHERE   friend_one_pk = :user_pk
    AND     is_active = 1
    UNION
    SELECT  friend_one_pk
    FROM    friendship
    WHERE   friend_two_pk = :user_pk
    AND     is_active = 1
)
"""

FRIENDSHIP_SQL = """
SELECT  *
FROM    friendship
WHERE   (
    (friend_one_pk = :u1_pk AND friend_two_pk = :u2_pk) OR 
    (friend_one_pk = :u2_pk AND friend_two_pk = :u1_pk)
)
AND     is_active = 1
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

INCOMING_FRIEND_REQUESTS_SQL = """
SELECT incoming_requests.from_pk, users.username, incoming_requests.message_txt, incoming_requests.timestamp_dt, incoming_requests.pk
FROM users, (
    SELECT *
    FROM friend_requests
    WHERE to_pk = :user_pk
    AND is_accepted = 0
    AND is_rejected = 0
) AS incoming_requests
WHERE users.pk = incoming_requests.from_pk
ORDER BY incoming_requests.timestamp_dt DESC
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

NUMBER_OF_ACTIVE_FRIEND_REQUESTS_SQL = """
SELECT  Count(*) as number_of_active_friend_requests
FROM    friend_requests
WHERE   ((from_pk = :user_one_pk AND to_pk = :user_two_pk) OR 
        (from_pk = :user_two_pk AND to_pk = :user_one_pk))
AND     is_accepted = 0
AND     is_rejected = 0
"""

NUMBER_OF_FRIENDS_SQL = """
SELECT Count(*) AS number_of_friends
FROM users
WHERE pk IN (
    SELECT  friend_two_pk
    FROM    friendship
    WHERE   friend_one_pk = :user_pk
    AND     is_active = 1
    UNION
    SELECT  friend_one_pk
    FROM    friendship
    WHERE   friend_two_pk = :user_pk
    AND     is_active = 1
)
"""

NUMBER_OF_INCOMING_FRIEND_REQUESTS_SQL = """
SELECT  Count(*) AS incoming_friend_requests
FROM    friend_requests
WHERE   to_pk = :user_pk
AND     is_accepted = 0
AND     is_rejected = 0
"""

NUMBER_OF_OUTCOMING_FRIEND_REQUESTS_SQL = """
SELECT  Count(*) AS outcoming_friend_requests
FROM    friend_requests
WHERE   from_pk = :user_pk
AND     is_accepted = 0
AND     is_rejected = 0
"""

OUTCOMING_FRIEND_REQUESTS_SQL = """
SELECT outcoming_requests.from_pk, users.username, outcoming_requests.message_txt, outcoming_requests.timestamp_dt, outcoming_requests.pk
FROM users, (
    SELECT *
    FROM friend_requests
    WHERE from_pk = :user_pk
    AND is_accepted = 0
    AND is_rejected = 0
) AS outcoming_requests
WHERE users.pk = outcoming_requests.to_pk
ORDER BY outcoming_requests.timestamp_dt DESC
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
