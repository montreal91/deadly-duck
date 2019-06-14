
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


class _DdPlayerCoach:
    """A passive data structure to bind player and coach level."""

    player: DdPlayer
    coach_level: int

    def __init__(self, player: DdPlayer, coach_level: int):
        self.player = player
        self.coach_level = coach_level


class DdClub:
    """A club in the tournament."""

    COACH_LEVELS = (0, 1, 2, 3)

    _is_controlled: bool
    _name: str
    _players: List[_DdPlayerCoach]
    _selected_coach: int
    _selected_player: Optional[int]
    _surface: str

    def __init__(self, name: str, surface: str):
        self._is_controlled = False
        self._name = name
        self._players = []
        self._selected_coach = 1
        self._selected_player = None
        self._surface = surface

    @property
    def is_controlled(self):
        """Checks if club us controlled by some user."""

        return self._is_controlled

    @property
    def name(self) -> str:
        """Club name."""

        return self._name

    @property
    def needs_decision(self) -> bool:
        """Checks if the club needs a decision made by user."""

        return self._is_controlled and self._selected_player is None

    @property
    def players(self) -> List[_DdPlayerCoach]:
        """List of club players."""
        return self._players

    @property
    def selected_player(self) -> DdPlayer:
        """Player selected for the next match."""

        def RawPlayers():
            return [p.player for p in self._players]

        if self._selected_player is None:
            return max(RawPlayers(), key=PlayerModelComparator)
        return self._players[self._selected_player].player

    @property
    def surface(self) -> str:
        """Court surface where club plays its home matches."""

        return self._surface

    def AddPlayer(self, player: DdPlayer):
        """Adds player to the club."""

        self._players.append(_DdPlayerCoach(player, 0))

    def ExpelRetiredPlayers(self):
        """Removes players from the club which are too old to play."""

        retirement_age = DdGameplayConstants.RETIREMENT_AGE.value
        def AgeCheck(player_slot: _DdPlayerCoach):
            return player_slot.player.age < retirement_age

        self._players = [p for p in self._players if AgeCheck(p)]

    def PerformPractice(self):
        """Performs player practice."""

        for plr in self._players:
            plr.player.AddExperience(
                plr.player.current_stamina * plr.coach_level
            )

    def PopPlayer(self, index: int):
        """Removes player from the club."""

        self._players.pop(index)

    def SelectCoach(self, coach_index: int, player_index: int):
        """
        Selects a coach.

        Possible coach indexes are 0, 1, 2, 3.
        """

        self._players[player_index].coach_level = self.COACH_LEVELS[coach_index]

    def SelectPlayer(self, index: Optional[int]):
        """Selects player for the next match."""

        self._selected_player = index

    def SetControlled(self, val: bool):
        """Sets club controlled or uncontrolled by a human user."""

        self._is_controlled = val
