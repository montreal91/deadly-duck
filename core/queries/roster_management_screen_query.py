"""
Created August 17, 2026

@author montreal91
"""
from typing import List
from typing import NamedTuple
from typing import Optional


class RosterManagementScreenQuery(NamedTuple):
    game_id: str
    manager_club_id: int


class PlayerRosterInfo(NamedTuple):
    player_id: int
    name: str
    level: int
    technique: float
    endurance: float
    age: int
    contract_cost: Optional[int]


class RosterManagementScreenQueryResult(NamedTuple):
    success: bool
    message: str
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
            )

        context = game.get_context(query.manager_club_id)
        roster = [
            _player_slot_to_roster_info(player_slot, player_id)
            for player_id, player_slot in enumerate(context["user_players"])
        ]

        return RosterManagementScreenQueryResult(
            success=True,
            message="Ok",
            roster=roster,
        )


def _player_slot_to_roster_info(player_slot, player_id):
    player = player_slot.player
    contract_cost = None
    if not player_slot.has_next_contract:
        contract_cost = player_slot.contract_cost

    return PlayerRosterInfo(
        player_id=player_id,
        name=f"{player.first_name} {player.last_name}",
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        age=player.age,
        contract_cost=contract_cost,
    )
