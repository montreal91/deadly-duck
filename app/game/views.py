
from flask                      import flash, g, redirect
from flask                      import render_template, request, url_for
from flask.ext.login            import current_user, login_required

from .                          import game
from ..                         import db

from config_game                import club_names

from app.custom_queries         import CURRENT_MATCH_SQL
from app.custom_queries         import STANDINGS_FOR_DIVISION_SQL
from app.custom_queries         import STANDINGS_SQL
from app.game.game_context      import DdGameContext
from app.game.league            import DdLeague
from app.game.match_processor   import DdMatchProcessor
from app.models                 import DdClub, DdMatch, DdPlayer, DdUser


@game.route( "/start-new-career/" )
@login_required
def StartNewCareer():
    if current_user.managed_club_pk is None:
        divisions = []
        for div in club_names:
            res = DdClub.query.filter_by( division_n=div )
            divisions.append( res.all() )
        DdLeague.CreateScheduleForUser( current_user )
        DdPlayer.CreatePlayersForUser( current_user )
        return render_template( "game/start_new_career.html", divisions=divisions )
    else:
        return redirect( url_for( "main.Index" ) )


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
        players = DdPlayer.query.filter( 
            DdPlayer.user_pk == current_user.pk
        ).filter( 
            DdPlayer.club_pk == current_user.managed_club_pk
        ).all()
        match = db.engine.execute( 
            CURRENT_MATCH_SQL.format( 
                current_user.managed_club_pk,
                current_user.current_season_n,
                current_user.current_day_n,
                current_user.pk
            )
        ).fetchall()

        if len( match ) > 0:
            match = match[0]
        else:
            match = []

        return render_template( 
            "game/main_screen.html",
            club=club,
            match=match,
            players=players
        )
    else:
        return redirect( url_for( "main.Index" ) )

@game.route( "/select_player/" )
@login_required
def SelectPlayerScreen():
    if current_user.pk not in game.contexts:
        AddRostersToContext( current_user )
    players = game.contexts[current_user.pk].GetClubRoster( 
        current_user.managed_club_pk
    )
    return render_template( "game/select_player.html", players=players )

@game.route( "/select_player/<int:pk>/" )
@login_required
def SelectPlayer( pk ):
    plr = DdPlayer.query.get( pk )
    assert plr.club_pk == current_user.managed_club_pk
    game.selected_players[current_user.pk] = plr.proxy
    return redirect( url_for( "game.MainScreen" ) )

@game.route( "/nextday/" )
@login_required
def NextDay():
    assert current_user.managed_club_pk is not None
    if current_user.pk not in game.selected_players or game.selected_players[current_user.pk] is None:
        flash( "You should choose player to play next match first." )
        return redirect( url_for( "game.MainScreen" ) )
    if current_user.current_day_n > current_user.season_last_day:
        StartNextSeason( current_user )
        flash( "Season #{0:d} is started.".format( 
            current_user.current_season_n
        ) )
        return redirect( url_for( "game.MainScreen" ) )

    today_matches = DdMatch.query.filter( 
        DdMatch.season_n == current_user.current_season_n
    ).filter( 
        DdMatch.day_n == current_user.current_day_n
    ).all()
    for match in today_matches:
        ProcessMatch( current_user, match )

    current_user.current_day_n += 1
    db.session.add( current_user )
    db.session.commit()
    game.selected_players[current_user.pk] = None
    return redirect( 
        url_for( 
            ".DayResults",
            season=current_user.current_season_n,
            day=current_user.current_day_n - 1
        )
    )


@game.route( "/day/<season>/<day>/" )
@login_required
def DayResults( season, day ):
    today_matches = DdMatch.query.filter( 
        DdMatch.season_n == season
    ).filter( 
        DdMatch.day_n == day
    ).filter( 
        DdMatch.user_pk == current_user.pk
    ).all()
    if len( today_matches ) == 0:
        return redirect( url_for( "game.MainScreen" ) )
    else:
        return render_template( 
            "game/dayresults.html",
            matches=today_matches,
            season=season,
            day=day
        )


@game.route( "/standings/<int:season>/" )
@login_required
def Standings( season ):
    if season > current_user.current_season_n:
        return redirect( 
            url_for( 
                "game.Standings",
                season=current_user.current_season_n
            )
        )
    table = db.engine.execute( 
        STANDINGS_SQL.format( 
            season,
            current_user.pk
        )
    ).fetchall()
    return render_template( 
        "game/standings.html",
        table=table,
        season=season
    )

@game.route( "/standings/<int:season>/div<int:division>/" )
@login_required
def DivisionStandings( season, division ):
    if season > current_user.current_season_n or not 0 < division < 3:
        return redirect( 
            url_for( 
                "game.Standings",
                season=current_user.current_season_n
            )
        )
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

@game.route( "/club/<int:club_pk>/" )
@login_required
def ClubDetails( club_pk ):
    club = DdClub.query.get_or_404( club_pk )
    players = []
    if current_user.pk in game.contexts:
        players = game.contexts[current_user.pk].GetClubRoster( club_pk )
    else:
        players = DdPlayer.query.filter( 
            DdPlayer.club_pk == club_pk
        ).filter( 
            DdPlayer.user_pk == current_user.pk
        ).all()
        players = [player.proxy for player in players]
    return render_template( 
        "game/club_details.html",
        club=club,
        players=players
    )


@game.route( "/player/<int:player_pk>/" )
@login_required
def PlayerDetails( player_pk ):
    player = DdPlayer.query.get_or_404( player_pk )
    matches = DdPlayer.GetPlayerRecentMatches( 
        player_pk,
        current_user.current_season_n
    )
    return render_template( 
        "game/player_details.html",
        player=player.proxy,
        club=player.club,
        matches=matches,
        show=player.club_pk == current_user.managed_club_pk
    )

def StartNextSeason( user ):
    user.current_season_n += 1
    user.current_day_n = 0
    db.session.add( user )
    db.session.commit()
    DdLeague.CreateScheduleForUser( user )

def PlayerProxyComparator( player_proxy ):
    return player_proxy.skill

def ProcessMatch( user, match ):
    home_player, away_player = None, None
    ctx = game.contexts[user.pk]
    if match.home_team_pk == user.managed_club_pk:
        home_player = game.selected_players[user.pk]
        ai_players = ctx.GetClubRoster( match.away_team_pk )
        away_player = max( ai_players, key=PlayerProxyComparator )
    elif match.away_team_pk == user.managed_club_pk:
        ai_players = ctx.GetClubRoster( match.home_team_pk )
        home_player = max( ai_players, key=PlayerProxyComparator )
        away_player = game.selected_players[user.pk]
    else:
        home_ai = ctx.GetClubRoster( match.home_team_pk )
        away_ai = ctx.GetClubRoster( match.away_team_pk )
        home_player = max( home_ai, key=PlayerProxyComparator )
        away_player = max( away_ai, key=PlayerProxyComparator )
    result = DdMatchProcessor.ProcessMatch( home_player, away_player, 2 )
    match.home_sets_n = result.home_sets
    match.away_sets_n = result.away_sets
    match.home_games_n = result.home_games
    match.away_games_n = result.away_games
    match.home_player_pk = home_player.pk
    match.away_player_pk = away_player.pk
    match.full_score_c = result.full_score
    match.is_played = True
    db.session.add( match )
    db.session.commit()

def AddRostersToContext( user ):
    clubs = DdClub.query.all()
    ctx = DdGameContext()
    for club in clubs:
        players = DdPlayer.query.filter( 
            DdPlayer.user_pk == user.pk
        ).filter( 
            DdPlayer.club_pk == club.club_id_n
        ).all()
        proxies = [player.proxy for player in players]
        ctx.SetClubRoster( club_pk=club.club_id_n, players_list=proxies )
    game.contexts[user.pk] = ctx
