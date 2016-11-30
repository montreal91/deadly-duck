
from decimal import Decimal

from app.data.game.club import DdDaoClub
from app.data.game.club_financial_account import DdClubFinancialAccount
from app.data.game.club_financial_account import DdDaoClubFinancialAccount
from app.data.game.match import DdDaoMatch
from app.data.game.player import DdDaoPlayer

class DdGameService( object ):
    def __init__( self ):
        self._dao_club = DdDaoClub()
        self._dao_club_financial_account = DdDaoClubFinancialAccount()
        self._dao_player = DdDaoPlayer()
        self._dao_match = DdDaoMatch()

    def AddFunds( self, user_pk=0, club_pk=0, funds=0.0 ):
        self._dao_club_financial_account.AddFunds( user_pk, club_pk, funds )

    def AgeUpAllActivePlayers( self, user ):
        players = self._dao_player.GetAllActivePlayers( user.pk )
        for player in players:
            player.AgeUp()
        self._dao_player.SavePlayers( players )

    def CreateNewcomersForUser( self, user ):
        self._dao_player.CreateNewcomersForUser( user )

    def CreateNewMatch( self, user_pk=0, season=0, day=0, home_team_pk=0, away_team_pk=0 ):
        return self._dao_match.CreateNewMatch(
            user_pk=user_pk,
            season=season,
            day=day,
            home_team_pk=home_team_pk,
            away_team_pk=away_team_pk
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

    def InsertClubs( self ):
        self._dao_club.InsertClubs()

    def GetClub( self, club_pk ):
        return self._dao_club.GetClub( club_pk )

    def GetAllActivePlayers( self, user_pk ):
        return self._dao_player.GetAllActivePlayers( user_pk )

    def GetAllClubs( self ):
        return self._dao_club.GetAllClubs()

    def GetAllClubsInDivision( self, division ):
        return self._dao_club.GetAllClubsInDivision( division )

    def GetCurrentMatch( self, user ):
        return self._dao_match.GetCurrentMatch( user )

    def GetFinancialAccount( self, user_pk=0, club_pk=0 ):
        return self._dao_club_financial_account.GetFinancialAccount( user_pk, club_pk )

    def GetFreeAgents( self, user_pk ):
        return self._dao_player.GetFreeAgents( user_pk )

    def GetNewcomersProxiesForUser( self, user ):
        return self._dao_player.GetNewcomersProxiesForUser( user )

    def GetPlayer( self, player_pk ):
        return self._dao_player.GetPlayer( player_pk )

    def GetRecentStandings( self, user ):
        return self._dao_match.GetRecentStandings( user )

    def GetTodayMatches( self, user ):
        return self._dao_match.GetTodayMatches( user )

    def SaveAccount( self, account ):
        self._dao_club_financial_account.SaveAccount( account )

    def SaveMatch( self, match=None ):
        self._dao_match.SaveMatch( match=match )

    def SaveMatches( self, matches=[] ):
        self._dao_match.SaveMatches( matches=matches )

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        return self._dao_player.GetClubPlayers( user_pk, club_pk )

    def GetDayResults( self, user_pk, season, day ):
        return self._dao_match.GetDayResults( user_pk, season, day )

    def GetDivisionStandings( self, user_pk=0, season=0, division=0 ):
        return self._dao_match.GetDivisionStandings(
            user_pk=user_pk,
            season=season,
            division=division
        )

    def GetLeagueStandings( self, user_pk=0, season=0 ):
        return self._dao_match.GetLeagueStandings(
            user_pk=user_pk,
            season=season
        )

    def GetPlayerRecentMatches( self, player_pk=0, season=0 ):
        return self._dao_player.GetPlayerRecentMatches(
            player_pk,
            season
        )

    def CreatePlayersForUser( self, user ):
        self._dao_player.CreatePlayersForUser( user )

    def SavePlayer( self, player ):
        self._dao_player.SavePlayer( player )

    def SavePlayers( self, players=[] ):
        self._dao_player.SavePlayers( players )

    def SaveRosters( self, rosters={} ):
        self._dao_player.SaveRosters( rosters )

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

    def _MatchIncome( self, sets=0 ):
        if sets == 2:
            return 1000
        elif sets == 1:
            return 700
        elif sets == 0:
            return 450
        else:
            raise ValueError( "Incorrect number of sets." )
