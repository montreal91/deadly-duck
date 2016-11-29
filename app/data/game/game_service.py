
from app.data.game.club import DdDaoClub
from app.data.game.match import DdDaoMatch
from app.data.game.player import DdDaoPlayer

class DdGameService( object ):
    def __init__( self ):
        self._dao_club = DdDaoClub()
        self._dao_player = DdDaoPlayer()
        self._dao_match = DdDaoMatch()

    def AgeUpAllActivePlayers( self, user ):
        players = self._dao_player.GetAllActivePlayers( user.pk )
        for player in players:
            player.AgeUp()
        self._dao_player.SavePlayers( players )

    def CreateNewcomersForUser( self, user ):
        self._dao_player.CreateNewcomersForUser( user )

    def CreateNewMatch( self, user_pk=0, season=0, day=0, home_team_pk=0, away_team_pk=0 ):
        return self._dao_match.CreateNewMatch( user_pk=user_pk, season=season, day=day, home_team_pk=home_team_pk, away_team_pk=away_team_pk )

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

    def GetNewcomersProxiesForUser( self, user ):
        return self._dao_player.GetNewcomersProxiesForUser( user )

    def GetPlayer( self, player_pk ):
        return self._dao_player.GetPlayer( player_pk )

    def GetRecentStandings( self, user ):
        return self._dao_match.GetRecentStandings( user )

    def GetTodayMatches( self, user ):
        return self._dao_match.GetTodayMatches( user )

    def SaveMatch( self, match=None ):
        self._dao_match.SaveMatch( match=match )

    def SaveMatches( self, matches=[] ):
        self._dao_match.SaveMatches( matches=matches )

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        return self._dao_player.GetClubPlayers( user_pk, club_pk )

    def GetDayResults( self, user_pk, season, day ):
        return self._dao_match.GetDayResults( user_pk, season, day )

    def GetDivisionStandings( self, user_pk=0, season=0, division=0 ):
        return self._dao_match.GetDivisionStandings( user_pk=user_pk, season=season, division=division )

    def GetLeagueStandings( self, user_pk=0, season=0 ):
        return self._dao_match.GetLeagueStandings( user_pk=user_pk, season=season )

    def GetPlayerRecentMatches( self, player_pk=0, season=0 ):
        return self._dao_player.GetPlayerRecentMatches( player_pk, season )

    def CreatePlayersForUser( self, user ):
        self._dao_player.CreatePlayersForUser( user )

    def SaveMatches( self, matches=[] ):
        self._dao_match.SaveMatches( matches )

    def SavePlayers( self, players=[] ):
        self._dao_player.SavePlayers( players )

    def SaveRosters( self, rosters={} ):
        self._dao_player.SaveRosters( rosters )
