"""
Created August 17, 2026

@author montreal91
"""
from typing import List
from typing import NamedTuple
from typing import Optional

from configuration.config_game import DdGameplayConstants


class RosterManagementScreenQuery(NamedTuple):
    game_id: str
    manager_club_id: str


class PlayerRosterInfo(NamedTuple):
    player_id: str
    pos: int
    name: str
    level: int
    technique: float
    endurance: float
    age: int
    contract_cost: Optional[int]
    contract_status: str


class RosterManagementScreenQueryResult(NamedTuple):
    success: bool
    message: str
    balance: int
    roster: List[PlayerRosterInfo]


class RosterManagementScreenQueryHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, query):
        game = self._game_repository.get_game(query.game_id)

        if game is None:
            return RosterManagementScreenQueryResult(
                success=False,
                message=f"Game with id={query.game_id} not found",
                roster=[],
                balance=0,
            )

        context = game.get_context(query.manager_club_id)
        roster = [
            _player_slot_to_roster_info(player_slot, player_pos)
            for player_pos, player_slot in enumerate(context["user_players"])
        ]

        return RosterManagementScreenQueryResult(
            success=True,
            message="Ok",
            roster=roster,
            balance=context["balance"],
        )


def _player_slot_to_roster_info(player_slot, player_pos):
    player = player_slot.player
    contract_cost = None
    contract_status = "Signed"
    next_age = player.age + 1
    is_last_season = next_age >= DdGameplayConstants.RETIREMENT_AGE.value

    if not player_slot.has_next_contract and not is_last_season:
        contract_cost = player_slot.contract_cost
        contract_status = str(player_slot.contract_cost)
    elif is_last_season:
        contract_status = "Not Available"

    return PlayerRosterInfo(
        player_id=player.player_id,
        pos=player_pos,
        name=f"{player.first_name} {player.last_name}",
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        age=player.age,
        contract_cost=contract_cost,
        contract_status=contract_status,
    )
