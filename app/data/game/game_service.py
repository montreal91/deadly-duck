
import logging

from decimal import Decimal
from random import choice
from random import randint

from sqlalchemy import text

from app import db
from app import cache
from app.custom_queries import GLOBAL_USER_RATING_SQL
from app.data.game.cache_keys import DdGameCacheKeys
from app.data.game.club import DdDaoClub
from app.data.game.club_financial_account import DdClubFinancialAccount
from app.data.game.club_financial_account import DdDaoClubFinancialAccount
from app.data.game.club_record import DdDaoClubRecord
from app.data.game.club_record import PlayoffRecordComparator
from app.data.game.club_record import RegularRecordComparator
from app.data.game.drafter import DdDrafter
from app.data.game.match import DdDaoMatch
from app.data.game.match import DdMatchStatuses
from app.data.game.player import DdDaoPlayer
from app.data.game.player import DdPlayer
from app.data.game.playoff_series import DdDaoPlayoffSeries
from app.data.game.playoff_series import DdPlayoffSeries
from app.data.game.skill import DdDaoSkill

from config_game import DdLeagueConfig
from config_game import DdRatingsParamerers
from config_game import DdTrainingTypes
from config_game import club_names
from config_game import INTENSIVITY_PERCENTAGES
from app.data.game.training_session import DdTrainingSession


class DdGameService( object ):
    def __init__( self ):
        self._dao_club = DdDaoClub()
        self._dao_club_financial_account = DdDaoClubFinancialAccount()
        self._dao_club_record = DdDaoClubRecord()
        self._dao_match = DdDaoMatch()
        self._dao_player = DdDaoPlayer()
        self._dao_playoff_series = DdDaoPlayoffSeries()
        self._dao_skill = DdDaoSkill()

    def AddFunds( self, user_pk=0, club_pk=0, funds=0.0 ):
        self._dao_club_financial_account.AddFunds( user_pk, club_pk, funds )

    def AgeUpAllActivePlayers( self, user ):
        players = self._dao_player.GetAllActivePlayers( user.pk )
        for player in players:
            player.AgeUp()
        self._dao_player.SavePlayers( players )

    def CreateNewcomersForUser( self, user_pk: int ) -> None:
        first_names, last_names = DdPlayer.GetNames()
        clubs = len( club_names[1] + club_names[2] )
        number_of_new_players = randint( clubs * 2, clubs * 4 )
        players, skills = [], []
        for i in range( number_of_new_players ): # @UnusedVariable
            endurance = self._dao_skill.GenerateNewSkill()
            technique = self._dao_skill.GenerateNewSkill()
            player = self._dao_player.CreatePlayer( 
                first_name=choice( first_names ),
                second_name=choice( first_names ),
                last_name=choice( last_names ),
                user_pk=user_pk,
                endurance=endurance,
                technique=technique
            )
            players.append( player )
            skills.append( endurance )
            skills.append( technique )
        self._dao_skill.SaveSkills( skills )
        self.SavePlayers( players )

    def CreateNewMatch( 
        self,
        user_pk=0,
        season=0,
        day=0,
        home_team_pk=0,
        away_team_pk=0,
    ):
        return self._dao_match.CreateNewMatch( 
            user_pk=user_pk,
            season=season,
            day=day,
            home_team_pk=home_team_pk,
            away_team_pk=away_team_pk
        )

    def CreateNewPlayoffRound( 
        self,
        user=None,
        div1_list=[],
        div2_list=[],
        current_round=0,
        final=False
    ):
        assert len( div1_list ) == len( div2_list )
        length = len( div1_list )
        if final:
            top, low = 0, 0
            recent_standings = self._dao_match.GetRecentStandings( user, for_draft=False )
            if recent_standings.index( div1_list[0] ) > recent_standings.index( div2_list[0] ):
                top = div1_list[0]
                low = div2_list[0]
            elif recent_standings.index( div1_list[0] ) < recent_standings.index( div2_list[0] ):
                top = div2_list[0]
                low = div1_list[0]
            else:
                raise ValueError

            series = self._dao_playoff_series.CreatePlayoffSeries( 
                top_seed_pk=top,
                low_seed_pk=low,
                round_n=current_round,
                user=user
            )
            self._dao_playoff_series.SavePlayoffSeries( series )
            self._CreateMatchesForSeriesList( 
                series_list=[series],
                first_day=user.current_day_n + DdLeagueConfig.GAP_DAYS
            )
            return
        new_series = []
        for i in range( int( length / 2 ) ):
            series = DdPlayoffSeries()
            series.top_seed_pk = div1_list[i]
            series.low_seed_pk = div1_list[length - i - 1]
            series.user_pk = user.pk
            series.season_n = user.current_season_n
            series.round_n = current_round
            new_series.append( series )

        for i in range( int( length / 2 ) ):
            series = DdPlayoffSeries()
            series.top_seed_pk = div2_list[i]
            series.low_seed_pk = div2_list[length - i - 1]
            series.user_pk = user.pk
            series.season_n = user.current_season_n
            series.round_n = current_round
            new_series.append( series )

        self._dao_playoff_series.SavePlayoffSeriesList( new_series )
        self._CreateMatchesForSeriesList( 
            series_list=new_series,
            first_day=user.current_day_n + DdLeagueConfig.GAP_DAYS
        )

    def CreateStartingAccounts( self, user ):
        accounts = []
        clubs = self._dao_club.GetAllClubs()
        for club in clubs:
            acc = DdClubFinancialAccount()
            acc.club_pk = club.club_id_n
            acc.user_pk = user.pk
            acc.money_nn = 500.0
            accounts.append( acc )
        self._dao_club_financial_account.SaveAccounts( accounts=accounts )

    def DoesUserNeedToSelectPlayer( self, user ):
        selected_player = self.GetSelectedPlayerForNextMatch( user.pk )
        current_match = self.GetCurrentMatch( user )
        return current_match and not selected_player

    def EndDraft( self, user_pk ):
        key = DdGameCacheKeys.DRAFTER.value.format( user_pk=user_pk ) # @UndefinedVariable
        drafter = cache.Get( key ) # Tricky point, but should be OKay
        self.SavePlayers( drafter.drafted_newcomers )
        cache.DeleteKey( key )


    def GetClub( self, club_pk ):
        return self._dao_club.GetClub( club_pk )

    def GetAllActivePlayers( self, user_pk ):
        return self._dao_player.GetAllActivePlayers( user_pk )

    def GetAllClubs( self ):
        return self._dao_club.GetAllClubs()

    def GetAllClubsInDivision( self, division ):
        return self._dao_club.GetAllClubsInDivision( division )

    def GetAllPlayoffSeries( self, user=None ):
        return self._dao_playoff_series.GetAllPlayoffSeries( user=user )

    def GetBestClubRecord( self, user=None, club_pk=0 ):
        playoff_records = self._dao_club_record.GetPlayoffRecords( club_pk=club_pk, user=user )
        if len( playoff_records ) != 0:
            return max( playoff_records, key=PlayoffRecordComparator )

        regular_records = self._dao_club_record.GetRegularRecords( club_pk=club_pk, user=user )
        if len( regular_records ) != 0:
            return max( regular_records, key=RegularRecordComparator )
        else:
            return None

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        return self._dao_player.GetClubPlayers( user_pk=user_pk, club_pk=club_pk )

    def GetClubPlayersPks( self, user_pk=0, club_pk=0 ):
        return self._dao_player.GetClubPlayersPks( user_pk, club_pk )

    def GetClubRecordsForUser( self, club_pk=0, user=None ):
        return self._dao_club_record.GetClubRecordsForUser( club_pk=club_pk, user=user )

    def GetCurrentMatch( self, user ):
        return self._dao_match.GetCurrentMatch( user )

    def GetDayResults( self, user_pk, season, day ):
        return self._dao_match.GetDayResults( user_pk, season, day )

    def GetDivisionStandings( self, user_pk=0, season=0, division=0 ):
        return self._dao_match.GetDivisionStandings( 
            user_pk=user_pk,
            season=season,
            division=division
        )

    def GetDrafter( self, user ) -> DdDrafter:
        key = DdGameCacheKeys.DRAFTER.value.format( user_pk=user.pk ) # @UndefinedVariable
        drafter = cache.Get( key )
        if drafter is None:
            newcomers = self.GetNewcomersSnapshotsForUser( user_pk=user.pk )
            standings = self.GetRecentStandings( user=user, for_draft=True )
            drafter = DdDrafter( 
                user_pk=user.pk,
                user_club_pk=user.managed_club_pk,
                remaining_newcomers=newcomers,
                standings=standings
            )
            cache.SetKey( key=key, value=drafter )
        return drafter

    def GetFinancialAccount( self, user_pk=0, club_pk=0 ):
        return self._dao_club_financial_account.GetFinancialAccount( user_pk, club_pk )

    def GetFreeAgents( self, user_pk ):
        return self._dao_player.GetFreeAgents( user_pk )

    def GetLeagueStandings( self, user_pk=0, season=0 ):
        return self._dao_match.GetLeagueStandings( 
            user_pk=user_pk,
            season=season
        )

    def GetListOfClubPrimaryKeys( self ):
        return self._dao_club.GetListOfClubPrimaryKeys()

    # TODO: move it to some DAO. Service should not have direct access to database.
    def GetGlobalRatings( self ):
        return db.engine.execute( # @UndefinedVariable
            text( GLOBAL_USER_RATING_SQL ).params( 
                precision=DdRatingsParamerers.PRECISION,
                matches_coefficient=DdRatingsParamerers.MATCHES_COEFFICIENT,
                round_coefficient=DdRatingsParamerers.ROUND_COEFFICIENT,
                ground_level=DdRatingsParamerers.GROUND_LEVEL,
                regular_points_factor=DdRatingsParamerers.REGULAR_POINTS_FACTOR
            )
        ).fetchall() # @UndefinedVariable

    def GetMaxPlayoffRound( self, user=None ):
        return self._dao_playoff_series.GetMaxPlayoffRound( user=user )

    def GetNewcomersSnapshotsForUser( self, user_pk: int ) -> list:
        return self._dao_player.GetNewcomersSnapshotsForUser( user_pk )

    def GetNumberOfActivePlayers( self ):
        return self._dao_player.GetNumberOfActivePlayers()

    def GetNumberOfFinishedMatches( self ):
        return self._dao_match.GetNumberOfFinishedMatches()

    def GetNumberOfFinishedSeries( self ):
        return self._dao_playoff_series.GetNumberOfFinishedSeries()

    def GetNumberOfUndraftedPlayers( self, user_pk: int ) -> int:
        return self._dao_player.GetNumberOfUndraftedPlayers( user_pk=user_pk )

    def GetPlayer( self, player_pk ):
        return self._dao_player.GetPlayer( player_pk )

    def GetPlayoffSeries( self, series_pk=0 ):
        return self._dao_playoff_series.GetPlayoffSeries( series_pk=series_pk )

    def GetPlayoffSeriesByRoundAndDivision( self, user=None, rnd=0 ):
        return self._dao_playoff_series.GetPlayoffSeriesByRoundAndDivision( 
            user=user,
            rnd=rnd
        )

    def GetPlayerRecentMatches( self, player_pk=0, season=0 ):
        return self._dao_player.GetPlayerRecentMatches( 
            player_pk,
            season
        )

    def GetRecentStandings( self, user, for_draft=False ):
        return self._dao_match.GetRecentStandings( user, for_draft=for_draft )

    def GetRemainingClubs( self, user ):
        div1standings, div2standings = self._GetClubsQualifiedToPlayoffs( user=user )

        series_list = self.GetAllPlayoffSeries( user=user )
        if len( series_list ) == 0:
            return div1standings, div2standings

        for series in series_list:
            l_pk = series.GetLooserPk( 
                sets_to_win=DdLeagueConfig.SETS_TO_WIN,
                matches_to_win=DdLeagueConfig.MATCHES_TO_WIN
            )
            if l_pk is None:
                raise ValueError( "Playoff series #{0:d} is not finished.".format( series.pk ) )
            if l_pk in div1standings:
                div1standings.pop( div1standings.index( l_pk ) )
            elif l_pk in div2standings:
                div2standings.pop( div2standings.index( l_pk ) )
            else:
                raise ValueError( 
                    "Club #{0:d} has lost in playoff series #{1:d} but not even qualified to playoffs.".format( 
                        l_pk,
                        series.pk
                    )
                )
        return div1standings, div2standings

    def GetSelectedPlayerForNextMatch( self, user_pk ):
        key = DdGameCacheKeys.SELECTED_PLAYER.value.format( # @UndefinedVariable
            user_pk=user_pk
        )
        return cache.Get( key )


    def GetTodayMatches( self, user ):
        return self._dao_match.GetTodayMatches( user )

    def InsertClubs( self ):
        self._dao_club.InsertClubs()

    def NewSeasonCondition( self, d1=[], d2=[] ):
        condition1 = len( d1 ) == 1 and len( d2 ) == 0
        condition2 = len( d2 ) == 1 and len( d1 ) == 0
        return condition1 or condition2

    def ProcessDailyRecovery( self, user_pk=0, played_players=[] ):
        """
        Restores stamina for active players of given user 'at the end of the day'.
        Important: saves changes to database. 
        :param user_pk: primary key of user, whose players need to be recovered.
        :param played_players: list of players who was playing matches this day.
        """
        played_players_pks = [plr.pk_n for plr in played_players]
        players_to_update = []
        club_pks = self.GetListOfClubPrimaryKeys()
        for cpk in club_pks:
            club_players = self.GetClubPlayers( user_pk=user_pk, club_pk=cpk )
            for plr in club_players:
                if plr.current_stamina_n < plr.max_stamina and plr.pk_n not in played_players_pks:
                    players_to_update.append( plr )
        players_to_update += played_players
        for plr in players_to_update:
            recovered_stamina = randint( 
                plr.max_stamina // 8,
                plr.max_stamina // 4
            )
            plr.RecoverStamina( recovered_stamina )
        self.SavePlayers( players_to_update )

    def ProcessTrainingSession( self, user_pk: int ) -> None:
        """
        Processes training sessions for players, which user decided to train.
        NOTE: Saves changes to database.
        :param user_pk:
        """
        key = DdGameCacheKeys.TRAINING_SESSION.value.format( user_pk=user_pk ) # @UndefinedVariable
        training_session = cache.Get( key )
        if training_session is None:
            return

        players_to_update = []
        t_sessions = training_session.training_sessions
        for player_pk in t_sessions:
            player = self.GetPlayer( player_pk )
            self._ProcessTrainingSessionForPlayer( 
                player=player,
                session=t_sessions[player_pk]
            )
            players_to_update.append( player )
        self.SavePlayers( players_to_update )
        cache.DeleteKey( key )


    def SaveAccount( self, account ):
        self._dao_club_financial_account.SaveAccount( account )

    def SaveClubRecords( self, user=None ):
        clubs = self._dao_club.GetAllClubs()
        records = []
        for club in clubs:
            rec = self._MakeClubRecord( club_pk=club.club_id_n, user=user )
            records.append( rec )
        self._dao_club_record.SaveClubRecords( club_records=records )

    def SaveMatch( self, match=None ):
        self._dao_match.SaveMatch( match=match )

    def SaveMatches( self, matches=[] ):
        series_to_update = []
        for match in matches:
            series = match.playoff_series
            if series is None:
                # In case if it is not a playoffs match
                continue
            if series.top_seed_pk == match.home_team_pk:
                if match.home_sets_n > match.away_sets_n:
                    series.top_seed_victories_n += 1
                elif match.home_sets_n < match.away_sets_n:
                    series.low_seed_victories_n += 1
                else:
                    raise ValueError( "Match score is incorrect. \n (Draw is impossible)." )
            elif series.top_seed_pk == match.away_team_pk:
                if match.home_sets_n > match.away_sets_n:
                    series.low_seed_victories_n += 1
                elif match.home_sets_n < match.away_sets_n:
                    series.top_seed_victories_n += 1
                else:
                    raise ValueError( "Match score is incorrect. \n (Draw is impossible)." )
            else:
                raise ValueError

            series_to_update.append( series )
        self.SavePlayoffSeriesList( series_to_update )
        self._dao_match.SaveMatches( matches=matches )


    def SavePlayer( self, player ):
        self._dao_player.SavePlayer( player )

    def SavePlayers( self, players=[] ):
        self._dao_player.SavePlayers( players )

    def SavePlayoffSeriesList( self, series_list=[] ):
        matches_to_abort = []
        for series in series_list:
            if not series.IsFinished( matches_to_win=DdLeagueConfig.MATCHES_TO_WIN ):
                continue

            for match in series.matches:
                if match.status_en == DdMatchStatuses.planned:
                    match.status_en = DdMatchStatuses.aborted
                    matches_to_abort.append( match )

        self._dao_match.SaveMatches( matches=matches_to_abort )
        self._dao_playoff_series.SavePlayoffSeriesList( series_list=series_list )


    def SaveRosters( self, rosters={} ):
        self._dao_player.SaveRosters( rosters )


    def SetPlayerForTraining( self, user_pk, player_pk, training_type, training_intensity ):
        key = DdGameCacheKeys.TRAINING_SESSION.value.format( user_pk=user_pk ) # @UndefinedVariable
        training_session = cache.Get( key )
        if training_session is None:
            training_session = DdTrainingSession()
        training_session.AddPlayerTraining( 
            player_pk,
            training_type,
            training_intensity
        )
        cache.SetKey( key=key, value=training_session )


    def StartDraftForUser( self, user ) -> None:
        if self.GetNumberOfUndraftedPlayers( user_pk=user.pk ) == 0:
            self.CreateNewcomersForUser( user.pk )
        newcomers = self.GetNewcomersSnapshotsForUser( user_pk=user.pk )
        drafter = DdDrafter( 
            user_pk=user.pk,
            user_club_pk=user.managed_club_pk,
            remaining_newcomers=newcomers,
            standings=self.GetRecentStandings( user=user, for_draft=True )
        )
        key = DdGameCacheKeys.DRAFTER.value.format( # @UndefinedVariable
            user_pk=user.pk
        )
        cache.SetKey( key=key, value=drafter )

    def SetPlayerForNextMatch( self, user_pk=0, player_pk=0 ):
        key = DdGameCacheKeys.SELECTED_PLAYER.value.format( # @UndefinedVariable
            user_pk=user_pk,
        )
        cache.SetKey( key=key, value=player_pk )


    def UnsetPlayerForNextMatch( self, user_pk=0 ):
        key = DdGameCacheKeys.SELECTED_PLAYER.value.format( # @UndefinedVariable
            user_pk=user_pk
        )
        cache.DeleteKey( key )

    def UpdateAccountsAfterMatch( self, matches=[] ):
        accounts = []
        for match in matches:
            home_account = self._dao_club_financial_account.GetFinancialAccount( 
                match.user_pk,
                match.home_team_pk
            )
            money = self._MatchIncome( match.home_sets_n ) - match.home_player.match_salary
            home_account.money_nn += Decimal( money )
            accounts.append( home_account )

            away_account = self._dao_club_financial_account.GetFinancialAccount( 
                match.user_pk,
                match.away_team_pk
            )
            money = self._MatchIncome( match.away_sets_n ) - match.away_player.match_salary
            away_account.money_nn += Decimal( money )
            accounts.append( away_account )
        self._dao_club_financial_account.SaveAccounts( accounts )

    def UpdateAccountsDaily( self, user ):
        clubs = self._dao_club.GetAllClubs()
        accounts = []
        for club in clubs:
            account = self._dao_club_financial_account.GetFinancialAccount( 
                user_pk=user.pk,
                club_pk=club.club_id_n
            )
            club_players = self._dao_player.GetClubPlayers( 
                user_pk=user.pk,
                club_pk=club.club_id_n
            )
            pay = sum( plr.passive_salary for plr in club_players )
            account.money_nn -= Decimal( pay )
            accounts.append( account )
        self._dao_club_financial_account.SaveAccounts( accounts=accounts )

    def UpdateDrafter( self, user_pk: int, drafter: DdDrafter ) -> None:
        key = DdGameCacheKeys.DRAFTER.value.format( user_pk=user_pk ) # @UndefinedVariable
        cache.SetKey( key=key, value=drafter )


    def _CreateMatchesForSeriesList( self, series_list=[], first_day=0 ):
        new_matches = []
        for series in series_list:
            shift = series_list.index( series ) % 2
            for i in range( len( DdLeagueConfig.SERIES_TOP_HOME_PATTERN ) ):
                match = self._dao_match.CreateNewMatchForSeries( 
                    series=series,
                    day=first_day + i * 2 + shift,
                    top_home=DdLeagueConfig.SERIES_TOP_HOME_PATTERN[i]
                )
                new_matches.append( match )
        self._dao_match.SaveMatches( new_matches )

    def _GetClubsQualifiedToPlayoffs( self, user ):
        div1standings = [row.club_pk for row in self.GetDivisionStandings( user_pk=user.pk, season=user.current_season_n, division=1 )]
        div2standings = [row.club_pk for row in self.GetDivisionStandings( user_pk=user.pk, season=user.current_season_n, division=2 )]

        div1standings = div1standings[:DdLeagueConfig.DIV_CLUBS_IN_PLAYOFFS]
        div2standings = div2standings[:DdLeagueConfig.DIV_CLUBS_IN_PLAYOFFS]
        return div1standings, div2standings

    def _MakeClubRecord( self, club_pk=0, user=None ):
        logging.debug( 
            "Making club record for club {club_pk:d} of user {user_pk:d}".format( 
                club_pk=club_pk,
                user_pk=user.pk
            )
        )
        standings = self._dao_match.GetLeagueStandings( 
            user_pk=user.pk,
            season=user.current_season_n
        )

        club_record = [rec for rec in standings if rec.club_pk == club_pk]
        if len( club_record ) != 1:
            raise ValueError( "Standings data is incorrect" )

        club_record = club_record[0]
        club_position = standings.index( club_record ) + 1
        club_points = club_record.sets_won
        final_playoff_series = self._dao_playoff_series.GetFinalPlayoffSeriesForClubInSeason( 
            club_pk=club_pk,
            user=user
        )
        return self._dao_club_record.CreateClubRecord( 
            club_pk=club_pk,
            position=club_position,
            points=club_points,
            user=user,
            playoff_series=final_playoff_series
        )

    def _MatchIncome( self, sets=0 ):
        """
        Placeholder function
        """
        if sets == 2:
            return 1000
        elif sets == 1:
            return 700
        elif sets == 0:
            return 450
        else:
            raise ValueError( "Incorrect number of sets." )

    def _ProcessTrainingSessionForPlayer( self, player, session ):
        if session.archetype == DdTrainingTypes.ENDURANCE.value:
            max_exp = session.intensity ** 2 * 2
            min_exp = int( max_exp / 2 )
            exp = randint( min_exp, max_exp )
            stamina_factor = int( player.current_stamina_n ) / player.max_stamina
            player.endurance.AddExperience( 
                int( exp * player.endurance.talent_n * stamina_factor )
            )
            player.RemoveStaminaLostInMatch( 
                player.max_stamina * INTENSIVITY_PERCENTAGES[session.intensity]
            )
        elif session.archetype == DdTrainingTypes.TECHNIQUE.value:
            max_exp = session.intensity ** 2 * 2
            min_exp = int( max_exp / 2 )
            exp = randint( min_exp, max_exp )
            stamina_factor = int( player.current_stamina_n ) / player.max_stamina
            player.technique.AddExperience( 
                int( exp * player.technique.talent_n * stamina_factor )
            )
            player.RemoveStaminaLostInMatch( 
                player.max_stamina * INTENSIVITY_PERCENTAGES[session.intensity]
            )
