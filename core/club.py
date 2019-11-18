
"""
Created Apr 09, 2019

@author montreal91
"""

from typing import List
from typing import Optional
from typing import Tuple

from configuration.config_game import DdGameplayConstants
from core.attendance import DdCourt
from core.financial import DdFinancialAccount
from core.player import DdPlayer
from core.player import PlayerModelComparator
from core.serialization import DdField
from core.serialization import DdJsonable


class DdClubPlayerSlot(DdJsonable):
    """A passive data structure to store player-related data."""

    player: Optional[DdPlayer]
    coach_level: int
    contract_cost: int
    has_next_contract: bool

    _FIELD_MAP = (
        DdField("player", "player"),
        DdField("coach_level", "coach_level"),
        DdField("contract_cost", "contract_cost"),
        DdField("has_next_contract", "has_next_contract"),
    )

    def __init__(self, player: Optional[DdPlayer] = None, coach_level: int = 0):
        self.player = player
        self.coach_level = coach_level
        self.contract_cost = 0
        self.has_next_contract = False
        self.is_selected = False


class DdFameTracker:
    """
    A simple class to track club's fame over time.

    Fame degrades with time.
    """

    _WEIGHTS: Tuple[float, ...] = (0.2, 0.4, 0.6, 0.8, 1.0)
    _fame_queue: List[int]

    def __init__(self):
        self._fame_queue = [0 for _ in range(len(self._WEIGHTS))]

    @property
    def fame(self) -> int:
        """Calculates current fame."""

        return int(sum(x * y for x, y in zip(self._fame_queue, self._WEIGHTS)))

    def AddFameValue(self, value):
        """Adds new fame instance to the tracker."""

        self._fame_queue.pop(0)
        self._fame_queue.append(value)


class DdClub:
    """
    A club in the tournament.

    This class does not make any decisions, its sole purpose is bookkeeping of
    players, coaches, stadiums and stuff. 'AI' or open interface for 'AI'
    should be implemented somewhere else.
    """

    COACH_LEVELS = (0, 1, 2, 3)

    _account: DdFinancialAccount
    _court: DdCourt
    _fame_tracker: DdFameTracker
    _is_controlled: bool
    _name: str
    _players: List[DdClubPlayerSlot]
    _selected_player: Optional[int]
    _surface: str

    def __init__(self, name: str, surface: str, court: DdCourt):
        self._account = DdFinancialAccount()
        self._court = court
        self._fame_tracker = DdFameTracker()
        self._is_controlled = False
        self._name = name
        self._players = []
        self._selected_player = None
        self._surface = surface

    @property
    def account(self) -> DdFinancialAccount:
        """Club's financial accout."""

        return self._account

    @property
    def court(self) -> DdCourt:
        """Court where club's next home match will be held."""

        return self._court

    @court.setter
    def court(self, value: DdCourt):
        self._court = value

    @property
    def fame(self):
        """Club's fame."""

        return self._fame_tracker.fame

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
    def players(self) -> List[DdClubPlayerSlot]:
        """List of club players."""
        return self._players

    @property
    def selected_player(self) -> Optional[DdPlayer]:
        """Player selected for the next match."""

        raw_players = [p.player for p in self._players]

        if self._selected_player is None:
            return max(raw_players, key=PlayerModelComparator, default=None)
        return self._players[self._selected_player].player

    @property
    def surface(self) -> str:
        """Court surface where club plays its home matches."""

        return self._surface

    def AddFame(self, value: int):
        """Adds new fame instance to the club."""

        self._fame_tracker.AddFameValue(value)

    def AddPlayer(self, player: DdPlayer):
        """Adds player to the club."""

        self._players.append(DdClubPlayerSlot(player, 0))

    def ContractPlayer(self, player_pk):
        """Marks that a player has a contract for the next season."""

        self._players[player_pk].has_next_contract = True

    def ExpelRetiredPlayers(self):
        """Removes players from the club which are too old to play."""

        retirement_age = DdGameplayConstants.RETIREMENT_AGE.value
        def AgeCheck(player_slot: DdClubPlayerSlot) -> bool:
            return player_slot.player.age < retirement_age

        self._players = [p for p in self._players if AgeCheck(p)]

    def PerformPractice(self):
        """Performs player practice."""

        for plr in self._players:
            plr.player.AddExperience(
                plr.player.current_stamina * plr.coach_level
            )

    def PopPlayer(self, index: int) -> DdPlayer:
        """Removes player from the club."""

        return self._players.pop(index).player

    def SelectCoach(self, coach_index: int, player_index: int):
        """
        Selects a coach.

        Possible coach indexes are 0, 1, 2, 3.
        """

        self._players[player_index].coach_level = self.COACH_LEVELS[coach_index]

    def SelectPlayer(self, index: Optional[int]):
        """Selects player for the next match."""

        if self._selected_player is not None:
            self._players[self._selected_player].is_selected = False

        self._selected_player = index

        if index is not None:
            self._players[index].is_selected = True

    def SetControlled(self, val: bool):
        """Sets club controlled or uncontrolled by a human user."""

        self._is_controlled = val
