
import logging

from flask                      import flash, redirect
from flask                      import render_template, url_for
from flask                      import abort, current_app
from flask_login                import current_user, login_required

from .                          import game
from ..                         import db

from config_game                import club_names, DdPlayerSkills

from app.data.models            import DdUser
from app.game.league            import DdLeague
from app.game.match_processor   import DdMatchProcessor
from random import randint
from app.data.game.player import DdPlayerSnapshot


@game.route( "/start-new-career/<pk>/" )
@login_required
def ChooseManagedClub( pk ):
    if current_user.managed_club_pk is None:
        current_user.managed_club_pk = pk
        db.session.add( current_user ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable
        return redirect( url_for( "game.MainScreen" ) )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route( "/club/<int:club_pk>/" )
@login_required
def ClubDetails( club_pk ):
    club = game.service.GetClub( club_pk )
    account = game.service.GetFinancialAccount( user_pk=current_user.pk, club_pk=club_pk )
    players = []
    if current_user.pk in game.contexts:
        players = game.contexts[current_user.pk].GetClubRoster( club_pk )
    else:
        players = game.service.GetClubPlayers( current_user.pk, club_pk )
    records = game.service.GetClubRecordsForUser( club_pk=club_pk, user=current_user )
    return render_template( 
        "game/club_details.html",
        club=club,
        players=players,
        account=account,
        records=records,
    )


@game.route( "/day/<int:season>/<int:day>/" )
@login_required
def DayResults( season, day ):
    today_matches = game.service.GetDayResults( current_user.pk, season, day )
    logging.debug( 
        "Debugging is {debug:s}".format( 
            debug=str( current_app.config["DEBUG"] )
        )
    )
    if len( today_matches ) == 0:
        return redirect( url_for( "game.MainScreen" ) )
    else:
        return render_template( 
            "game/dayresults.html",
            matches=today_matches,
            season=season,
            day=day,
            debug=current_app.config["DEBUG"]
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


@game.route( "/draft/" )
@login_required
def Draft():
    if not current_user.pk in game.contexts or not game.contexts[current_user.pk].is_draft:
        abort( 403 )

    ctx = game.contexts[current_user.pk]
    while ctx.available_newcomers > 0:
        club_pk = ctx.GetPickingClubPk()
        if club_pk == current_user.managed_club_pk:
            return redirect( url_for( "game.PickScreen" ) )
        player = ctx.DoBestAiChoice()
        ctx.AddPlayerToClubRoster( club_pk, player )
        ctx.IncrementPickPointer()
    game.service.SaveRosters( ctx.rosters )
    ctx.EndDraft()
    flash( "Season #{0:d} is started".format( current_user.current_season_n ) )
    return redirect( url_for( "game.MainScreen" ) )



@game.route( "/fire_player/<int:player_pk>/" )
@login_required
def FirePlayer( player_pk ):
    player = game.service.GetPlayer( player_pk )
    if player.club_pk != current_user.managed_club_pk:
        abort( 403 )
    if len( game.service.GetClubPlayers( user_pk=current_user.pk, club_pk=current_user.managed_club_pk ) ) <= 2:
        flash( "You must have at least 2 players in your club." )
        return redirect( url_for( "game.PlayerDetails", player_pk=player_pk ) )
    player.club_pk = None
    game.service.SavePlayer( player )
    DdLeague.AddRostersToContext( current_user )
    return redirect( url_for( "game.PlayerDetails", player_pk=player_pk ) )


@game.route( "/free_agents/" )
@login_required
def FreeAgents():
    agents = game.service.GetFreeAgents( current_user.pk )
    return render_template( "game/free_agents.html", agents=agents )


@game.route( "/hire_player/<int:player_pk>/" )
@login_required
def HirePlayer( player_pk ):
    player = game.service.GetPlayer( player_pk )
    if player.club_pk is not None:
        abort( 403 )
    player.club_pk = current_user.managed_club_pk
    game.service.SavePlayer( player )
    DdLeague.AddRostersToContext( current_user )
    return redirect( url_for( "game.PlayerDetails", player_pk=player_pk ) )


@game.route( "/main/" )
@login_required
def MainScreen():
    logging.debug( "User {pk:d} is on main screen".format( pk=current_user.pk ) )
    if current_user.managed_club_pk is not None:
        club = game.service.GetClub( current_user.managed_club_pk )
        DdLeague.AddRostersToContext( current_user )
        ctx = game.contexts[current_user.pk]
        if game.service.GetNumberOfUndraftedPlayers( current_user ) > 0:
            DdLeague.AddRostersToContext( current_user, ctx=ctx )
            DdLeague.StartDraft( current_user, ctx, need_to_create_newcomers=False )
            return redirect( url_for( "game.Draft" ) )
        players = ctx.GetClubRoster( 
            current_user.managed_club_pk
        )
        match = game.service.GetCurrentMatch( current_user )
        if match is not None and match.home_team_pk == current_user.managed_club_pk:
            ai_players = ctx.GetClubRoster( match.away_team_pk )
            away_player = max( ai_players, key=PlayerSnapshotComparator )
        else:
            away_player = None
        account = game.service.GetFinancialAccount( 
            current_user.pk,
            current_user.managed_club_pk
        )
        ctx.next_match = match is not None
        current_round = game.service.GetMaxPlayoffRound( user=current_user )
        return render_template( 
            "game/main_screen.html",
            club=club,
            match=match,
            players=players,
            away_player=away_player,
            account=account,
            current_round=current_round
        )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route( "/nextday/" )
@login_required
def NextDay():
    logging.debug( 
        "User {pk:d} plays next day. Season #{season:d}. Day #{day:d}".format( 
            pk=current_user.pk,
            season=current_user.current_season_n,
            day=current_user.current_day_n
        )
    )
    assert current_user.managed_club_pk is not None
    if current_user.pk not in game.contexts:
        DdLeague.AddRostersToContext( current_user )
    ctx = game.contexts[current_user.pk]
    if ctx.NeedToSelectPlayer():
        flash( "You have to select player to play next match." )
        return redirect( url_for( "game.MainScreen" ) )
    if current_user.current_day_n > current_user.season_last_day:
        remaining_d1, remaining_d2 = game.service.GetRemainingClubs( current_user )
        poff_round = game.service.GetMaxPlayoffRound( user=current_user )
        new_round_string = "PlayOff Round #{round:d} is started."
        if poff_round is None:
            # Start first round of play-off
            game.service.CreateNewPlayoffRound( 
                user=current_user,
                div1_list=remaining_d1,
                div2_list=remaining_d2,
                current_round=1,
                final=False
            )
            flash( new_round_string.format( round=1 ) )
            return redirect( url_for( "game.MainScreen" ) )
        elif len( remaining_d1 ) != 0 and len( remaining_d2 ) != 0:
            # Start later round of play-off
            game.service.CreateNewPlayoffRound( 
                user=current_user,
                div1_list=remaining_d1,
                div2_list=remaining_d2,
                current_round=poff_round + 1,
                final=len( remaining_d1 ) == 1
            )
            flash( new_round_string.format( round=poff_round + 1 ) )
            return redirect( url_for( "game.MainScreen" ) )
        elif game.service.NewSeasonCondition( d1=remaining_d1, d2=remaining_d2 ) is True:
            game.service.SaveClubRecords( user=current_user )
            DdLeague.StartNextSeason( current_user )
            DdLeague.StartDraft( current_user, ctx )
            flash( "Welcome to the entry draft." )
            return redirect( url_for( "game.Draft" ) )
        else:
            raise ValueError

    today_matches = game.service.GetTodayMatches( current_user )
    for match in today_matches:
        ProcessMatch( current_user, match )

    ProcessDailyRecovery( current_user )
    game.service.SaveMatches( today_matches )
    game.service.UpdateAccountsAfterMatch( today_matches )
    game.service.UpdateAccountsDaily( current_user )
    game.service.SyncListOfPlayersSnapshots( ctx.TakePlayersToUpdate() )
    current_user.current_day_n += 1
    db.session.add( current_user ) # @UndefinedVariable
    db.session.commit() # @UndefinedVariable
    ctx.selected_player = None
    return redirect( 
        url_for( 
            ".DayResults",
            season=current_user.current_season_n,
            day=current_user.current_day_n - 1
        )
    )


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


@game.route( "/pick/" )
@login_required
def PickScreen():
    if not current_user.pk in game.contexts or not game.contexts[current_user.pk].is_draft:
        abort( 403 )
    ctx = game.contexts[current_user.pk]
    return render_template( "game/pick_screen.html", players=ctx.newcomers )


@game.route( "/player/<int:player_pk>/" )
@login_required
def PlayerDetails( player_pk ):
    player = game.service.GetPlayer( player_pk )
    matches = game.service.GetPlayerRecentMatches( 
        player_pk,
        current_user.current_season_n
    )
    return render_template( 
        "game/player_details.html",
        player=player.snapshot,
        endurance=player.endurance,
        technique=player.technique,
        club=player.club,
        matches=matches,
        show=player.club_pk == current_user.managed_club_pk
    )


@game.route( "/playoffs/" )
@login_required
def Playoffs():
    current_round = game.service.GetMaxPlayoffRound( user=current_user )
    if current_round is None:
        return redirect( url_for( "game.MainScreen" ) )

    series_dict = {}
    for i in range( current_round ):
        series = game.service.GetPlayoffSeriesByRoundAndDivision( 
            user=current_user,
            rnd=i + 1
        )
        series_dict[i] = series
    return render_template( 
        "game/playoffs.html",
        series_dict=series_dict,
        season=current_user.current_season_n
    )

@game.route( "/user/<username>/playoff_series_details/<int:series_pk>/" )
@login_required
def PlayoffSeriesDetails( username, series_pk ):
    series = game.service.GetPlayoffSeries( series_pk=series_pk )
    user = DdUser.query.filter_by( username=username ).first() # @UndefinedVariable
    if user is None:
        abort( 404 )
    return render_template( "game/playoff_series_details.html", series=series )


@game.route( "/play_rest_of_season/" )
@login_required
def PlayRestOfSeason():
    assert current_user.managed_club_pk is not None
    ctx = game.contexts[current_user.pk]
    played_matches = []
    while current_user.current_day_n <= current_user.season_last_day:
        day_matches = game.service.GetTodayMatches( current_user )
        for match in day_matches:
            ProcessMatch( current_user, match, autoplay=True )
        played_matches += day_matches
        ProcessDailyRecovery( current_user )
        game.service.UpdateAccountsAfterMatch( matches=day_matches )
        game.service.UpdateAccountsDaily( current_user )
        current_user.current_day_n += 1
    game.service.SaveMatches( matches=played_matches )
    game.service.SyncListOfPlayersSnapshots( ctx.TakePlayersToUpdate() )
    db.session.add( current_user ) # @UndefinedVariable
    db.session.commit() # @UndefinedVariable
    return redirect( url_for( "game.Standings", season=current_user.current_season_n ) )

@game.route( "/select_player/<int:pk>/" )
@login_required
def SelectPlayer( pk ):
    if current_user.pk not in game.contexts:
        DdLeague.AddRostersToContext( current_user )
    ctx = game.contexts[current_user.pk]
    players = ctx.GetClubRoster( 
        current_user.managed_club_pk
    )
    # Hack!
    player = [plr for plr in players if plr.pk == pk]
    if len( player ) != 1:
        abort( 403 )
    ctx.selected_player = player[0]
    flash( 
        "{0:s}. {1:s}. {2:s} has been selected for the next game.".format( 
            ctx.selected_player.first_name[0],
            ctx.selected_player.second_name[0],
            ctx.selected_player.last_name
        )
    )
    return redirect( url_for( "game.MainScreen" ) )


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


@game.route( "/start-new-career/" )
@login_required
def StartNewCareer():
    if current_user.managed_club_pk is None:
        divisions = []
        for div in club_names:
            res = game.service.GetAllClubsInDivision( div )
            divisions.append( res )
        logging.debug( "Creating Schedule for user {pk:d}".format( pk=current_user.pk ) )
        DdLeague.CreateScheduleForUser( current_user )
        logging.debug( "Creating new players for user {pk:d}".format( pk=current_user.pk ) )
        game.service.CreateNewcomersForUser( current_user )
        logging.debug( "Create financial accounts for user {pk:d}".format( pk=current_user.pk ) )
        game.service.CreateStartingAccounts( current_user )
        return render_template( "game/start_new_career.html", divisions=divisions )
    else:
        return redirect( url_for( "main.Index" ) )


# Those methods should be static in DdGameService class
def PlayerSnapshotComparator( player_snapshot ):
    return player_snapshot.actual_technique


def ProcessDailyRecovery( user ):
    ctx = game.contexts[user.pk]
    rosters = game.contexts[user.pk].rosters
    for club in rosters:
        for player in rosters[club]:
            if player.current_stamina < player.max_stamina:
                recovered_stamina = randint( 
                    player.max_stamina // 8,
                    player.max_stamina // 4
                )
                player.RecoverStamina( recovered_stamina )
                ctx.AddPlayerToUpdate( player )


def ProcessMatch( user, match, autoplay=False ):
    home_player, away_player = None, None
    ctx = game.contexts[user.pk]
    if match.home_team_pk == user.managed_club_pk and not autoplay:
        home_player = ctx.selected_player
        ai_players = ctx.GetClubRoster( match.away_team_pk )
        away_player = max( ai_players, key=PlayerSnapshotComparator )
    elif match.away_team_pk == user.managed_club_pk and not autoplay:
        ai_players = ctx.GetClubRoster( match.home_team_pk )
        home_player = max( ai_players, key=PlayerSnapshotComparator )
        away_player = ctx.selected_player
    else:
        home_ai = ctx.GetClubRoster( match.home_team_pk )
        away_ai = ctx.GetClubRoster( match.away_team_pk )
        home_player = max( home_ai, key=PlayerSnapshotComparator )
        away_player = max( away_ai, key=PlayerSnapshotComparator )
    match_processor = DdMatchProcessor()
    result = match_processor.ProcessMatch( home_player, away_player, 2 )
    match.home_sets_n = result.home_sets
    match.away_sets_n = result.away_sets
    match.home_games_n = result.home_games
    match.away_games_n = result.away_games
    match.home_player_pk = home_player.pk
    match.away_player_pk = away_player.pk
    match.full_score_c = result.full_score
    match.is_played = True
    match.SetFinishedStatus()

    home_player.RemoveStaminaLostInMatch( result.home_stamina_lost )
    away_player.RemoveStaminaLostInMatch( result.away_stamina_lost )
    home_player.AddEnduranceExperience( result.home_stamina_lost )
    away_player.AddEnduranceExperience( result.away_stamina_lost )

    home_experience = DdPlayerSnapshot.CalculateMatchTechniqueExperience( 
        games_lost=result.away_games,
        games_won=result.home_games,
        sets_lost=result.away_sets,
        sets_won=result.home_sets
    )
    away_experience = DdPlayerSnapshot.CalculateMatchTechniqueExperience( 
        games_lost=result.home_games,
        games_won=result.away_games,
        sets_lost=result.home_sets,
        sets_won=result.away_sets
    )
    home_player.AddTechniqueExperience( home_experience )
    away_player.AddTechniqueExperience( away_experience )

    ctx.AddPlayerToUpdate( home_player )
    ctx.AddPlayerToUpdate( away_player )
