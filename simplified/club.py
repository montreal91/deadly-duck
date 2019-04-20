
"""
Created Apr 09, 2019

@author montreal91
"""

from typing import List
from typing import Optional
from typing import Tuple

from configuration.config_game import DdGameplayConstants
from simplified.player import DdPlayer
from simplified.player import PlayerModelComparator


class DdClub:
    """A club in the tournament."""

    def __init__(self, name: str):
        self._name = name
        self._players = []
        self._selected_player = None
        self._practice_match = None

    @property
    def name(self) -> str:
        """Club name."""
        return self._name

    @property
    def players(self) -> List[DdPlayer]:
        """List of club players."""

        return self._players

    @property
    def practice_match(self) -> Optional[Tuple[DdPlayer, DdPlayer]]:
        """If set, returns a pair of players for practice."""

        if self._practice_match is None:
            return None
        return (
            self._players[self._practice_match[0]],
            self._players[self._practice_match[1]]
        )

    @property
    def selected_player(self) -> DdPlayer:
        """Player selected for the next match."""

        if self._selected_player is None:
            return max(self._players, key=PlayerModelComparator)
        return self._players[self._selected_player]

    def AddPlayer(self, player: DdPlayer):
        """Adds player to the club."""

        self._players.append(player)

    def ExpelRetiredPlayers(self):
        """Removes players from the club which are too old to play."""

        retirement_age = DdGameplayConstants.RETIREMENT_AGE.value
        self._players = [p for p in self._players if p.age < retirement_age]

    def PopPlayer(self, index: int):
        """Removes player from the club."""

        self._players.pop(index)

    def SelectPlayer(self, index: int):
        """Selects player for the next match."""

        self._selected_player = index

    def SetPractice(self, i1: int, i2: int):
        """Selects players for the practice match."""

        assert i1 != i2
        assert 0 <= i1 < len(self._players)
        assert 0 <= i2 < len(self._players)
        self._practice_match = (i1, i2)

    def SortPlayers(self):
        """
        Obviously, sorts players.

        Added for convenience.
        """

        self._players.sort(key=lambda p: p.age)

    def UnsetPractice(self):
        """Unselects players for the practice match."""

        self._practice_match = None
