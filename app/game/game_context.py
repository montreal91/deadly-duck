
class DdGameContext( object ):
    def __init__( self ):
        super( DdGameContext, self ).__init__()

        self._rosters = {}
        self._newcomers = []
        self._standings = []
        self._pick_pointer = 0
        self._is_draft = False
        self._next_match = True
        self._selected_player = None

    @property
    def available_newcomers( self ):
        return len( self._newcomers )

    @property
    def is_draft( self ):
        return self._is_draft

    @is_draft.setter
    def is_draft( self, val ):
        self._is_draft = val

    @property
    def next_match( self ):
        return self._next_match

    @next_match.setter
    def next_match( self, val ):
        self._next_match = bool( val )

    @property
    def rosters( self ):
        return self._rosters

    @property
    def selected_player( self ):
        return self._selected_player

    @selected_player.setter
    def selected_player( self, val ):
        self._selected_player = val

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

    def NeedToSelectPlayer( self ):
        return self._next_match and not self._selected_player
