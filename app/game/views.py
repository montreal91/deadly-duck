
from random             import choice

from flask              import render_template, redirect, request
from flask              import url_for, flash
from flask.ext.login    import login_required, current_user

from .                  import game
from ..                 import db
from ..models           import DdUser, DdClub, DdMatch
from config_game        import club_names
from app.game.league    import DdLeague

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
) AS played
FROM clubs
ORDER BY sets DESC, games DESC
"""

@game.route( "/start-new-career/" )
@login_required
def StartNewCareer():
    if current_user.managed_club_pk is None:
        divisions = []
        for div in club_names:
            res = DdClub.query.filter_by( division_n=div )
            divisions.append( res.all() )
        DdLeague.CreateScheduleForUser( current_user )
        return render_template( "game/start_new_career.html", divisions=divisions )
    else:
        return redirect(url_for("main.Index"))


@game.route( "/start-new-career/<pk>/" )
@login_required
def ChooseManagedClub( pk ):
    if current_user.managed_club_pk is None:
        current_user.managed_club_pk = pk
        db.session.add( current_user )
        db.session.commit()

        return redirect( url_for( "game.MainScreen" ) )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route( "/main/" )
@login_required
def MainScreen():
    if current_user.managed_club_pk is not None:
        club = DdClub.query.get( current_user.managed_club_pk )
        match = db.engine.execute(
            CURRENT_MATCH_SQL.format(
                current_user.managed_club_pk,
                current_user.current_season_n,
                current_user.current_day_n
            )
        ).fetchall()
        return render_template( "game/main_screen.html", club=club, match=match[0] )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route("/nextday/")
@login_required
def NextDay():
    assert current_user.managed_club_pk is not None
    today_matches = DdMatch.query.filter(
        DdMatch.season_n == current_user.current_season_n
    ).filter(
        DdMatch.day_n == current_user.current_day_n
    ).all()
    for match in today_matches:
        res = QuickSimResult()
        match.home_sets_n = res[0]
        match.away_sets_n = res[1]
        match.is_played = True

    current_user.current_day_n += 1
    db.session.add_all(today_matches)
    db.session.add(current_user)
    db.session.commit()
    return redirect(
        url_for(
            ".DayResults",
            season=current_user.current_season_n,
            day=current_user.current_day_n - 1
        )
    )

@game.route("/day/<season>/<day>/")
@login_required
def DayResults(season, day):
    today_matches = DdMatch.query.filter(
        DdMatch.season_n == season
    ).filter(
        DdMatch.day_n == day
    ).all()
    return render_template(
        "game/dayresults.html",
        matches=today_matches,
        season=season,
        day=day
    )

@game.route("/standings/<int:season>/")
@login_required
def Standings(season):
    table = db.engine.execute(STANDINGS_SQL.format(season, current_user.pk)).fetchall()
    return render_template(
        "game/standings.html",
        table=table,
        season=season
    )


def QuickSimResult():
    possible_outcomes = [(2, 0), (2, 1), (0, 2), (1, 2)]
    return choice(possible_outcomes)
