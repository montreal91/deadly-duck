
"""
Created Apr 09, 2019

@author montreal91
"""

from typing import List

from simplified.player import DdPlayer
from simplified.player import PlayerModelComparator


class DdClub:
    """A club in the tournament."""

    def __init__(self, name: str):
        self._name = name
        self._players = []
        self._selected_player = None

    @property
    def name(self) -> str:
        """Club name."""
        return self._name

    @property
    def players(self) -> List[DdPlayer]:
        """List of club players."""

        return self._players

    @property
    def selected_player(self) -> DdPlayer:
        """Player selected for the next match."""

        if self._selected_player is None:
            return max(self._players, key=PlayerModelComparator)
        return self._players[self._selected_player]

    def AddPlayer(self, player: DdPlayer):
        """Adds player to the club."""

        self._players.append(player)

    def PopPlayer(self, index: int):
        """Removes player from the club."""

        self._players.pop(index)

    def SelectPlayer(self, index: int):
        """Selects player for the next match."""

        self._selected_player = index
