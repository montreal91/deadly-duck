
MAX_DAY_IN_SEASON_SQL = """
SELECT Max(day_n)
FROM   matches
WHERE  user_pk = {0:d}
AND    season_n = {1:d}
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
)
FROM matches
WHERE season_n = {1:d}
AND   day_n = {2:d}
AND   (home_team_pk = {0:d} OR away_team_pk = {0:d})
AND   user_pk = {3:d}
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
    AND   is_played = 1
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
    AND   is_played = 1
) AS games, (
    SELECT Count(*)
    FROM matches
    WHERE (home_team_pk = clubs.club_id_n OR away_team_pk = clubs.club_id_n)
    AND is_played = 1
    AND season_n = {0:d}
    AND user_pk = {1:d}
) AS played
FROM clubs
ORDER BY sets DESC, games DESC
"""

STANDINGS_FOR_DIVISION_SQL = STANDINGS_SQL[0:-31] + "WHERE division_n = {2:d}\n" + STANDINGS_SQL[-31:]

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
AND      is_played = 1
ORDER BY day_n DESC
LIMIT    {2:d}
"""

CLUB_PLAYERS_SQL = """
SELECT pk_n, first_name_c, second_name_c, last_name_c, skill_n, age_n, club_pk
FROM  players
WHERE user_pk = {0:d}
AND   club_pk = {1:d}
AND   is_active = 1
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
    SELECT skill_n
    FROM   players
    WHERE  players.pk_n = matches.home_player_pk
), (
    SELECT skill_n
    FROM   players
    WHERE  players.pk_n = matches.away_player_pk
), full_score_c
FROM matches
WHERE user_pk = {0:d} 
AND season_n = {1:d}
AND day_n = {2:d}
AND is_played = 1
"""
