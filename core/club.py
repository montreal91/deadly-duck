
"""
Created Apr 09, 2019

@author montreal91
"""

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from uuid import UUID

from configuration.config_game import DdGameplayConstants
from core.financial import DdFinancialAccount
from core.player import Player
from core.player import player_model_comparator
from core.serialization import DdField
from core.serialization import Jsonable


class ClubPlayerSlot(Jsonable):
    """A passive data structure to store player-related data."""

    player: Optional[Player]
    coach_level: int
    contract_cost: int
    has_next_contract: bool

    _FIELD_MAP = (
        DdField("player", "player"),
        DdField("coach_level", "coach_level"),
        DdField("contract_cost", "contract_cost"),
        DdField("has_next_contract", "has_next_contract"),
    )

    def __init__(self, player: Optional[Player] = None, coach_level: int = 0):
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

    def add_fame_value(self, value):
        """Adds new fame instance to the tracker."""

        self._fame_queue.pop(0)
        self._fame_queue.append(value)


class Club:
    """
    A club in the tournament.

    This class does not make any decisions, its sole purpose is bookkeeping of
    players, coaches, stadiums and stuff. 'AI' or open interface for 'AI'
    should be implemented somewhere else.
    """

    COACH_LEVELS = (0, 1, 2, 3)

    _club_id: str
    _account: DdFinancialAccount
    _fame_tracker: DdFameTracker
    _is_controlled: bool
    _name: str
    _players: Dict[UUID, ClubPlayerSlot]
    _selected_player: Optional[str]

    def __init__(
            self,
            club_id,
            game_id,
            name: str,
            coach_power: int
    ):
        self._club_id = club_id
        self._game_id = game_id
        self._account = DdFinancialAccount()
        self._fame_tracker = DdFameTracker()
        self._is_controlled = False
        self._name = name
        self._players = {}
        self._selected_player = None
        self._coach_power = coach_power

    @property
    def account(self) -> DdFinancialAccount:
        """Club's financial account."""

        return self._account

    @property
    def club_id(self) -> str:
        return self._club_id

    @property
    def game_id(self):
        return self._game_id

    @property
    def coach_power(self):
        return self._coach_power

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
    def has_selected_player(self) -> bool:
        return self._selected_player is not None

    @property
    def players(self) -> List[ClubPlayerSlot]:
        """List of club players."""
        return list(self._players.values())

    @property
    def selected_player(self) -> Optional[Player]:
        """Player selected for the next match."""

        raw_players = [p.player for p in self.players]

        if self._selected_player is None:
            return max(raw_players, key=player_model_comparator, default=None)
        selected_slot = self.get_player_slot(self._selected_player)
        if selected_slot is None:
            return max(raw_players, key=player_model_comparator, default=None)
        return selected_slot.player

    def add_fame(self, value: int):
        """Adds new fame instance to the club."""

        self._fame_tracker.add_fame_value(value)

    def add_player(self, player: Player):
        """Adds player to the club."""
        if self._is_controlled:
            coach_level = 0
        else:
            coach_level = self._coach_power
        self._players[_normalize_player_id(player.player_id)] = ClubPlayerSlot(
            player, coach_level
        )

    def contract_player(self, player_id):
        """Marks that a player has a contract for the next season."""

        player_slot = self.get_player_slot(player_id)
        if player_slot is not None:
            player_slot.has_next_contract = True

    def expel_retired_players(self):
        """Removes players from the club which are too old to play."""

        retirement_age = DdGameplayConstants.RETIREMENT_AGE.value
        def age_check(player_slot: ClubPlayerSlot) -> bool:
            return player_slot.player.age < retirement_age

        self._players = {
            player_id: player_slot
            for player_id, player_slot in self._players.items()
            if age_check(player_slot)
        }

    def perform_practice(self):
        """Performs player practice."""

        for plr in self.players:
            plr.player.AddExperience(
                plr.player.current_stamina * plr.coach_level
            )

    def pop_player(self, player_id: str) -> Player:
        """Removes player from the club."""

        return self._players.pop(_normalize_player_id(player_id)).player

    def select_coach(self, coach_index: int, player_id: str):
        """
        Selects a coach.

        Possible coach indexes are 0, 1, 2, 3.
        """

        player_slot = self.get_player_slot(player_id)
        if player_slot is not None:
            player_slot.coach_level = self.COACH_LEVELS[coach_index]

    def select_player(self, player_id: Optional[str]):
        """Selects player for the next match."""

        if self._selected_player is not None:
            selected_slot = self.get_player_slot(self._selected_player)
            if selected_slot is not None:
                selected_slot.is_selected = False

        self._selected_player = player_id

        if player_id is not None:
            selected_slot = self.get_player_slot(player_id)
            if selected_slot is not None:
                selected_slot.is_selected = True

    def get_player_slot(self, player_id: str) -> Optional[ClubPlayerSlot]:
        return self._players.get(_normalize_player_id(player_id))

    def has_player(self, player_id: str) -> bool:
        return self.get_player_slot(player_id) is not None

    def set_coach_power(self, val: int):
        if val in self.COACH_LEVELS:
            self._coach_power = val

            for slot in self.players:
                slot.coach_level = val


    def set_controlled(self, val: bool):
        """Sets club controlled or uncontrolled by a human user."""

        self._is_controlled = val

        for slot in self.players:
            slot.coach_level = 0


def _normalize_player_id(player_id) -> UUID:
    if isinstance(player_id, UUID):
        return player_id
    return UUID(player_id)
