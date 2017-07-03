"""
Created on Jun 26, 2017

@author: montreal91
"""

from app.exceptions import DdDraftPickException
from app.data.game.player import PlayerModelComparator

class DdDrafter( object ):
    """
    This is a helper class to process entry draft.
    """

    def __init__( 
            self,
            user_pk: int,
            user_club_pk: int,
            remaining_newcomers: list,
            standings: tuple
        ) -> None:
        """
        Constructor
        """
        self._remaining_newcomers = remaining_newcomers
        self._remaining_newcomers.sort( key=PlayerModelComparator )
        self._standings = standings
        self._drafted_newcomers = []
        self._user_pk = user_pk
        self._user_club_pk = user_club_pk
        self._pick_pointer = 0

    @property
    def is_draft_over( self ) -> bool:
        return len( self._remaining_newcomers ) == 0

    @property
    def drafted_newcomers( self ) -> list:
        if self.is_draft_over:
            return self._drafted_newcomers
        else:
            return None

    @property
    def remaining_newcomers( self ) -> list:
        return self._remaining_newcomers

    def ProcessDraft( self ) -> None:
        club_pk = self._GetPickingClubPk()
        while club_pk != self._user_club_pk and not self.is_draft_over:
            newcomer = self._remaining_newcomers.pop()
            newcomer.club_pk = club_pk
            newcomer.is_drafted = True
            self._drafted_newcomers.append( newcomer )
            self._IncrementPickPointer()
            club_pk = self._GetPickingClubPk()

    def PickPlayer( self, player_pk: int, club_pk: int ) -> None:
        player = [plr for plr in self._remaining_newcomers if plr.pk_n == player_pk]
        if player:
            player = player[0]
        else:
            raise DdDraftPickException( "User has tried to pick wrong player." )
        self._remaining_newcomers = [plr for plr in self._remaining_newcomers if plr.pk_n != player_pk]
        player.is_drafted = True
        player.club_pk = club_pk
        self._drafted_newcomers.append( player )
        self._IncrementPickPointer()

    def _GetPickingClubPk( self ) -> int:
        return self._standings[self._pick_pointer]

    def _IncrementPickPointer( self ) -> None:
        self._pick_pointer += 1
        self._pick_pointer %= len( self._standings )

