
class DdGameContext( object ):
    def __init__( self ):
        super( DdGameContext, self ).__init__()

        self._rosters = {}

    def SetClubRoster( self, club_pk=0, players_list=[] ):
        self._rosters[club_pk] = players_list

    def GetClubRoster( self, club_pk ):
        return self._rosters[club_pk]
