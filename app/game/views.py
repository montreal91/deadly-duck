
from flask                      import flash, g, redirect
from flask                      import render_template, request, url_for
from flask                      import abort
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
from app.data.models            import DdUser
from app.data.game.club         import DdClub
from app.data.game.match        import DdMatch
from app.data.game.player       import DdPlayer


@game.route( "/start-new-career/" )
@login_required
def StartNewCareer():
    if current_user.managed_club_pk is None:
        divisions = []
        for div in club_names:
            res = game.service.GetAllClubsInDivision( div )
            divisions.append( res )
        DdLeague.CreateScheduleForUser( current_user )
        game.service.CreatePlayersForUser( current_user )
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
        club = game.service.GetClub( current_user.managed_club_pk )
        if current_user.pk not in game.contexts:
            AddRostersToContext( current_user )
        players = game.contexts[current_user.pk].GetClubRoster( 
            current_user.managed_club_pk
        )
        match = game.service.GetCurrentMatch( current_user )
        game.contexts[current_user.pk].next_match = match is not None
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
    plr = game.service.GetPlayer( pk )
    assert plr.club_pk == current_user.managed_club_pk
    game.contexts[current_user.pk].selected_player = plr.snapshot
    return redirect( url_for( "game.MainScreen" ) )

@game.route( "/nextday/" )
@login_required
def NextDay():
    assert current_user.managed_club_pk is not None
    ctx = game.contexts[current_user.pk]
    if ctx.NeedToSelectPlayer():
        flash( "You should choose player to play next match first." )
        return redirect( url_for( "game.MainScreen" ) )
    if current_user.current_day_n > current_user.season_last_day:
        StartDraft( current_user )
        flash( "Welcome to the entry draft." )
        return redirect( url_for( "game.Draft" ) )

    today_matches = game.service.GetTodayMatches( current_user )
    for match in today_matches:
        ProcessMatch( current_user, match )

    game.service.SaveMatches( today_matches )
    current_user.current_day_n += 1
    db.session.add( current_user )
    db.session.commit()
    ctx.selected_player = None
    return redirect( 
        url_for( 
            ".DayResults",
            season=current_user.current_season_n,
            day=current_user.current_day_n - 1
        )
    )


@game.route( "/day/<int:season>/<int:day>/" )
@login_required
def DayResults( season, day ):
    today_matches = game.service.GetDayResults( current_user.pk, season, day )
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
        abort( 404 )
    table = game.service.GetLeagueStandings( user_pk=current_user.pk, season=season )
    return render_template( 
        "game/standings.html",
        table=table,
        season=season
    )

@game.route( "/standings/<int:season>/div<int:division>/" )
@login_required
def DivisionStandings( season, division ):
    if season > current_user.current_season_n or not 0 < division < 3:
        abort( 404 )
    table = game.service.GetDivisionStandings( user_pk=current_user.pk, season=season, division=division )
    return render_template( 
        "game/standings.html",
        table=table,
        season=season
    )

@game.route( "/club/<int:club_pk>/" )
@login_required
def ClubDetails( club_pk ):
    club = game.service.GetClub( club_pk )
    players = []
    if current_user.pk in game.contexts:
        players = game.contexts[current_user.pk].GetClubRoster( club_pk )
    else:
        players = game.service.GetClubPlayers( current_user.pk, club_pk )
    return render_template( 
        "game/club_details.html",
        club=club,
        players=players
    )

@game.route( "/draft/" )
@login_required
def Draft():
    if not current_user.pk in game.contexts or not game.contexts[current_user.pk].is_draft:
        abort( 403 )

    ctx = game.contexts[current_user.pk]
    while ctx.available_newcomers > 0:
        club_pk = ctx.GetPickingClubPk()
        if club_pk == current_user.managed_club_pk:
            # don't forget to increment pick_pointer when user picks a player
            return redirect( url_for( "game.PickScreen" ) )
        player = ctx.DoBestAiChoice()
        ctx.AddPlayerToClubRoster( club_pk, player )
        ctx.IncrementPickPointer()
    game.service.SaveRosters( ctx.rosters )
    ctx.EndDraft()
    StartNextSeason( current_user )
    flash( "Season #{0:d} is started".format( current_user.current_season_n ) )
    return redirect( url_for( "game.MainScreen" ) )


@game.route( "/pick/" )
@login_required
def PickScreen():
    if not current_user.pk in game.contexts or not game.contexts[current_user.pk].is_draft:
        abort( 403 )
    ctx = game.contexts[current_user.pk]
    return render_template( "game/pick_screen.html", players=ctx.GetNewcomers() )

@game.route( "/pick/<int:player_pk>/" )
@login_required
def PickPlayer( player_pk ):
    if not current_user.pk in game.contexts or not game.contexts[current_user.pk].is_draft:
        abort( 403 )
    ctx = game.contexts[current_user.pk]
    selected_player = ctx.PickPlayer( player_pk )
    ctx.AddPlayerToClubRoster( current_user.managed_club_pk, selected_player )
    ctx.IncrementPickPointer()
    return redirect( url_for( "game.Draft" ) )


@game.route( "/player/<int:player_pk>/" )
@login_required
def PlayerDetails( player_pk ):
    player = DdPlayer.query.get_or_404( player_pk )
    matches = game.service.GetPlayerRecentMatches( 
        player_pk,
        current_user.current_season_n
    )
    return render_template( 
        "game/player_details.html",
        player=player.snapshot,
        club=player.club,
        matches=matches,
        show=player.club_pk == current_user.managed_club_pk
    )

def StartNextSeason( user ):
    user.current_season_n += 1
    user.current_day_n = 0
    game.service.AgeUpAllActivePlayers( user )
    db.session.add( user )
    db.session.commit()
    DdLeague.CreateScheduleForUser( user )
    game.contexts[user.pk] = DdGameContext()
    AddRostersToContext( user )


def StartDraft( user ):
    if user.pk in game.contexts:
        ctx = game.contexts[user.pk]
    else:
        ctx = DdGameContext()

    ctx.is_draft = True
    game.service.CreateNewcomersForUser( current_user )
    newcomers = game.service.GetNewcomersProxiesForUser( current_user )
    ctx.SetNewcomers( newcomers )
    standings = game.service.GetRecentStandings( user )
    ctx.SetStandings( standings )
    game.contexts[user.pk] = ctx


def PlayerProxyComparator( player_proxy ):
    return player_proxy.skill

def ProcessMatch( user, match ):
    home_player, away_player = None, None
    ctx = game.contexts[user.pk]
    if match.home_team_pk == user.managed_club_pk:
        home_player = ctx.selected_player
        ai_players = ctx.GetClubRoster( match.away_team_pk )
        away_player = max( ai_players, key=PlayerProxyComparator )
    elif match.away_team_pk == user.managed_club_pk:
        ai_players = ctx.GetClubRoster( match.home_team_pk )
        home_player = max( ai_players, key=PlayerProxyComparator )
        away_player = ctx.selected_player
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
#     db.session.add( match )
#     db.session.commit()

def AddRostersToContext( user ):
    clubs = game.service.GetAllClubs()
    ctx = DdGameContext()
    for club in clubs:
        players = game.service.GetClubPlayers( user_pk=user.pk, club_pk=club.club_id_n )
        ctx.SetClubRoster( club_pk=club.club_id_n, players_list=players )
    game.contexts[user.pk] = ctx
