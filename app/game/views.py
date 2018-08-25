
import json
import logging

from flask                      import abort
from flask                      import current_app
from flask                      import flash
from flask                      import jsonify
from flask                      import redirect
from flask                      import render_template
from flask                      import request
from flask                      import url_for
from flask.views                import MethodView
from flask.views                import View
from flask_login                import current_user
from flask_login                import login_required

from app                        import db
from app.data.game.match        import MatchChronologicalComparator
from app.data.game.player       import DdPlayer
from app.data.game.player       import PlayerModelComparator
from app.data.models            import DdUser
from app.game                   import game
from app.game.league            import DdLeague
from app.game.match_processor   import DdMatchProcessor
from config_game                import club_names
from config_game                import DdTrainingIntensities
from config_game                import DdTrainingTypes


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
    players = game.service.GetClubPlayers( 
        user_pk=current_user.pk,
        club_pk=club_pk
    )
    records = game.service.GetClubRecordsForUser( club_pk=club_pk, user=current_user )
    return render_template( 
        "game/club_details.html",
        club=club,
        players=players,
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
    return redirect( url_for( "game.PlayerDetails", player_pk=player_pk ) )


@game.route( "/free_agents/" )
@login_required
def FreeAgents():
    agents = game.service.GetFreeAgents( user_pk=current_user.pk )
    return render_template( "game/free_agents.html", agents=agents )


@game.route( "/hire_player/<int:player_pk>/" )
@login_required
def HirePlayer( player_pk ):
    player = game.service.GetPlayer( player_pk )
    if player.club_pk is not None:
        abort( 403 )
    player.club_pk = current_user.managed_club_pk
    game.service.SavePlayer( player )
    return redirect( url_for( "game.PlayerDetails", player_pk=player_pk ) )


@game.route( "/main/" )
@login_required
def MainScreen():
    logging.debug( "User {pk:d} is on main screen".format( pk=current_user.pk ) )
    if current_user.managed_club_pk is None:
        return redirect( url_for( "main.Index" ) )

    club = game.service.GetClub( current_user.managed_club_pk )
    players = game.service.GetClubPlayers( 
        user_pk=current_user.pk,
        club_pk=current_user.managed_club_pk
    )
    players.sort( key=PlayerModelComparator, reverse=True )
    selected_player_pk = game.service.GetSelectedPlayerForNextMatch( 
        current_user.pk
    )
    if not selected_player_pk:
        selected_player_pk = -1

    match = game.service.GetCurrentMatch( current_user )
    if match is not None and match.home_team_pk == current_user.managed_club_pk:
        ai_players = game.service.GetClubPlayers( 
            user_pk=current_user.pk,
            club_pk=match.away_team_pk
        )
        away_player = max( ai_players, key=PlayerModelComparator )
    else:
        away_player = None
    current_round = game.service.GetMaxPlayoffRound( user=current_user )
    return render_template( 
        "game/main_screen.html",
        club=club,
        match=match,
        players=players,
        away_player=away_player,
        current_round=current_round,
        selected_player_pk=selected_player_pk
    )


# TODO: separate class-based views from method views
# and ajax from non-ajax views.
class DdNextDayView( View ):
    decorators = [login_required]
    def __init__( self ):
        super( DdNextDayView, self ).__init__()
        self._players_to_update = []

    def dispatch_request( self ):
        logging.debug( 
            "User {pk:d} plays next day. Season #{season:d}. Day #{day:d}".format( 
                pk=current_user.pk,
                season=current_user.current_season_n,
                day=current_user.current_day_n
            )
        )
        if game.service.DoesUserNeedToSelectPlayer( current_user ):
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
                game.service.StartNextSeason( user_pk=current_user.pk )
                DdLeague.StartNextSeason( current_user )
                return redirect( url_for( "game.MainScreen" ) )
            else:
                raise ValueError

        today_matches = game.service.GetTodayMatches( current_user )
        for match in today_matches:
            self.ProcessMatch( current_user, match )

        game.service.ProcessTrainingSession( user_pk=current_user.pk )
        game.service.ProcessDailyRecovery( 
            user_pk=current_user.pk,
            played_players=self._players_to_update
        )
        game.service.SaveMatches( today_matches )
        current_user.current_day_n += 1
        game.service.UnsetPlayerForNextMatch( current_user.pk )
        db.session.add( current_user ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable
        return redirect( 
            url_for( 
                ".DayResults",
                season=current_user.current_season_n,
                day=current_user.current_day_n - 1
            )
        )

    def ProcessMatch( self, user, match, autoplay=False ):
        home_player, away_player = None, None
        if match.home_team_pk == user.managed_club_pk and not autoplay:
            home_player = game.service.GetPlayer( 
                player_pk=game.service.GetSelectedPlayerForNextMatch( user_pk=current_user.pk )
            )
            ai_players = game.service.GetClubPlayers( user_pk=user.pk, club_pk=match.away_team_pk )
            away_player = max( ai_players, key=PlayerModelComparator )
        elif match.away_team_pk == user.managed_club_pk and not autoplay:
            ai_players = game.service.GetClubPlayers( user_pk=user.pk, club_pk=match.home_team_pk )
            home_player = max( ai_players, key=PlayerModelComparator )
            away_player = game.service.GetPlayer( 
                player_pk=game.service.GetSelectedPlayerForNextMatch( user_pk=current_user.pk )
            )
        else:
            home_ai = game.service.GetClubPlayers( user_pk=user.pk, club_pk=match.home_team_pk )
            away_ai = game.service.GetClubPlayers( user_pk=user.pk, club_pk=match.away_team_pk )
            home_player = max( home_ai, key=PlayerModelComparator )
            away_player = max( away_ai, key=PlayerModelComparator )
        match_processor = DdMatchProcessor()
        result = match_processor.ProcessMatch( home_player, away_player, 2 )
        match.home_sets_n = result.home_sets
        match.away_sets_n = result.away_sets
        match.home_games_n = result.home_games
        match.away_games_n = result.away_games
        match.home_player_pk = home_player.pk_n
        match.away_player_pk = away_player.pk_n
        match.full_score_c = result.full_score
        match.is_played = True
        match.SetFinishedStatus()

        home_player.RemoveStaminaLostInMatch( result.home_stamina_lost )
        away_player.RemoveStaminaLostInMatch( result.away_stamina_lost )

        home_experience = DdPlayer.CalculateNewExperience(
            result.home_sets,
            away_player
        )
        away_experience = DdPlayer.CalculateNewExperience(
            result.away_sets,
            home_player
        ) 

        home_player.AddExperience(home_experience)
        away_player.AddExperience(away_experience)

        home_player.LevelUpAuto()
        away_player.LevelUpAuto()

        self._players_to_update.append( home_player )
        self._players_to_update.append( away_player )

game.add_url_rule( "/nextday/", view_func=DdNextDayView.as_view( 'NextDay' ) )


@game.route( "/player/<int:player_pk>/" )
@login_required
def PlayerDetails( player_pk ):
    player = game.service.GetPlayer( player_pk=player_pk )
    matches = game.service.GetPlayerRecentMatches( 
        player_pk,
        current_user.current_season_n
    )
    return render_template( 
        "game/player_details.html",
        player=player,
        club=player.club,
        intensities=DdTrainingIntensities,
        matches=matches,
        show=player.club_pk == current_user.managed_club_pk,
        training_types=DdTrainingTypes
    )


class DdPlayoffs( MethodView ):
    decorators = [login_required]

    def get( self ):
        series_dict = {}
        return render_template( 
            "game/playoffs_draw.html",
            series_dict=series_dict,
            season=current_user.current_season_n
        )

    def post( self ):
        json_data = request.json
        season = int(json_data["season"])
        series = game.service.GetAllPlayoffSeries(
            user_pk=current_user.pk,
            season=season
        )
        series = [s.dictionary for s in series]
        return jsonify({"series": series})


game.add_url_rule( "/playoffs/", view_func=DdPlayoffs.as_view( "Playoffs" ) )


@game.route( "/playoff_series_details/<int:series_pk>/" )
@login_required
def PlayoffSeriesDetails( series_pk ):
    series = game.service.GetPlayoffSeries( series_pk=series_pk )
    series.matches.sort(key=MatchChronologicalComparator)
    return render_template( "game/playoff_series_details.html", series=series )


@game.route( "/select_player/<int:pk>/" )
@login_required
def SelectPlayer( pk ):
    # TODO: refactor this method.
    # It can be done much easier.
    players = game.service.GetClubPlayers( 
        user_pk=current_user.pk,
        club_pk=current_user.managed_club_pk
    )
    # Hack!
    player = [plr for plr in players if plr.pk_n == pk]
    if len( player ) != 1:
        abort( 403 )

    # player = player[0]
    game.service.SetPlayerForNextMatch( user_pk=current_user.pk, player_pk=pk )
    return redirect( url_for( "game.MainScreen" ) )


class DdSetTraining( MethodView ):
    decorators = [login_required]

    def post( self ):
        vals = json.loads( request.form["values"] )
        player = game.service.GetPlayer( player_pk=vals["pk"] )
        if player.club_pk != current_user.managed_club_pk or player.user_pk != current_user.pk:
            return jsonify( message="You can't set training for this user.", status=0 )

        training_type = vals["training_type"]
        training_intensity = int( vals["training_intensity"] )
        if not self._CheckCorrectTrainingType( training_type ):
            return jsonify( message="Incorrect training type.", status=0 )

        if not self._CheckCorrectTrainingIntensity( training_intensity ):
            return jsonify( message="Incorrect training intensity.", status=0 )

        game.service.SetPlayerForTraining( 
            user_pk=current_user.pk,
            player_pk=player.pk_n,
            training_type=training_type,
            training_intensity=training_intensity
        )
        return jsonify( message="OK", status=1 )

    def _CheckCorrectTrainingType( self, tt ):
        for item in DdTrainingTypes:
            if tt == item.value:
                return True
        return False

    def _CheckCorrectTrainingIntensity( self, ti ):
        for item in DdTrainingIntensities:
            if ti == item.value:
                return True
        return False


game.add_url_rule( "/_set_training/", view_func=DdSetTraining.as_view( "SetTraining" ) )



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
        game.service.CreateInitialPlayersForUser( current_user.pk )
        logging.debug( "Create financial accounts for user {pk:d}".format( pk=current_user.pk ) )
        game.service.CreateStartingAccounts( current_user )
        return render_template( "game/start_new_career.html", divisions=divisions )
    else:
        return redirect( url_for( "main.Index" ) )
