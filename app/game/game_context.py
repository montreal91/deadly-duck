
from app.models import DdPlayer

class DdGameContext( object ):
    def __init__( self ):
        super( DdGameContext, self ).__init__()

        self._rosters = {}
        self._newcomers = []
        self._standings = []
        self._pick_pointer = 0
        self._is_draft = False

    @property
    def available_newcomers( self ):
        return len( self._newcomers )

    @property
    def is_draft( self ):
        return self._is_draft

    @is_draft.setter
    def is_draft( self, val ):
        self._is_draft = val

    def SetClubRoster( self, club_pk=0, players_list=[] ):
        self._rosters[club_pk] = players_list

    def GetClubRoster( self, club_pk ):
        return self._rosters[club_pk]

    def SetNewcomers( self, newcomers=[] ):
        self._newcomers = newcomers

    def GetNewcomers( self ):
        return self._newcomers

    def SetStandings( self, standings=[] ):
        self._standings = standings

    def EndDraft( self ):
        self._newcomers = []
        self._standings = []
        self._is_draft = False

    def DropPickPointer( self ):
        self._pick_pointer = 0

    def PickPlayer( self, player_pk ):
        ind = [i for i, player in enumerate( self._newcomers ) if player.pk == player_pk][0]
        return self._newcomers.pop( ind )

    def AddPlayerToClubRoster( self, club_pk, player ):
        self._rosters[club_pk].append( player )

    def IncrementPickPointer( self ):
        self._pick_pointer += 1
        self._pick_pointer %= len( self._standings )

    def GetPickingClubPk( self ):
        return self._standings[self._pick_pointer]

    def DoBestAiChoice( self ):
        return self._newcomers.pop()

    def SaveRosters( self ):
        for club_pk in self._rosters:
            DdPlayer.SaveClubRoster( club_pk=club_pk, roster=self._rosters[club_pk] )
