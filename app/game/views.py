
from random             import choice

from flask              import render_template, redirect, request
from flask              import url_for, flash
from flask.ext.login    import login_required, current_user

from .                  import game
from ..                 import db
from app.game.league    import DdLeague
from app.custom_queries import CURRENT_MATCH_SQL, STANDINGS_SQL, STANDINGS_FOR_DIVISION_SQL
from app.models         import DdUser, DdClub, DdMatch
from config_game        import club_names


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
                current_user.current_day_n,
                current_user.pk
            )
        ).fetchall()
        if len(match) > 0:
            return render_template(
                "game/main_screen.html",
                club=club,
                match=match[0],
            )
        else:
            return render_template(
                "game/main_screen.html",
                club=club,
                match=[],
            )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route("/nextday/")
@login_required
def NextDay():
    assert current_user.managed_club_pk is not None
    if current_user.current_day_n > current_user.season_last_day:
        StartNextSeason(current_user)
        return redirect(url_for("game.MainScreen"))
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
    ).filter(
        DdMatch.user_pk == current_user.pk
    ).all()
    if len(today_matches) == 0:
        return redirect(url_for("game.MainScreen"))
    else:
        return render_template(
            "game/dayresults.html",
            matches=today_matches,
            season=season,
            day=day
        )


@game.route("/standings/<int:season>/")
@login_required
def Standings(season):
    if season > current_user.current_season_n:
        return redirect(url_for("game.Standings", season=current_user.current_season_n))
    table = db.engine.execute(STANDINGS_SQL.format(season, current_user.pk)).fetchall()
    return render_template(
        "game/standings.html",
        table=table,
        season=season
    )

@game.route("/standings/<int:season>/div<int:division>/")
@login_required
def DivisionStandings(season, division):
    if season > current_user.current_season_n or not 0 < division <3:
        return redirect(url_for("game.Standings", season=current_user.current_season_n))
        print(STANDINGS_FOR_DIVISION_SQL)
    table = db.engine.execute(
        STANDINGS_FOR_DIVISION_SQL.format(
            season,
            current_user.pk,
            division
        )
    ).fetchall()
    return render_template(
        "game/standings.html",
        table=table,
        season=season
    )

def StartNextSeason(user):
    user.current_season_n += 1
    user.current_day_n = 0
    db.session.add(user)
    db.session.commit()
    DdLeague.CreateScheduleForUser(user)


def QuickSimResult():
    possible_outcomes = [(2, 0), (2, 1), (0, 2), (1, 2)]
    return choice(possible_outcomes)
