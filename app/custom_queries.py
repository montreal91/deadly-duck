
MAX_DAY_IN_SEASON_SQL = """
SELECT Max(day_n)
FROM   matches
WHERE  user_pk = {0:d}
AND    season_n = {1:d}
"""

CURRENT_MATCH_SQL = """
SELECT (
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
