"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass
from typing import List
from typing import Optional

from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.player_assignment_repository import (
    PlayerAssignmentRepository,
)


@dataclass(frozen=True)
class RosterManagementScreenQuery:
    game_id: str
    manager_club_id: str


@dataclass(frozen=True)
class PlayerRosterInfo:
    player_id: str
    pos: int
    name: str
    level: int
    technique: float
    endurance: float
    age: int
    contract_cost: Optional[int]
    contract_status: str


@dataclass(frozen=True)
class RosterManagementScreenQueryResult:
    success: bool
    message: str
    balance: int
    main_roster: List[PlayerRosterInfo]
    farm_roster: List[PlayerRosterInfo]
    farm_club_id: str
    farm_club_name: str


class RosterManagementScreenQueryHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider,
            player_assignment_repository: PlayerAssignmentRepository,
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._player_assignment_repository = player_assignment_repository

    def __call__(self, query: RosterManagementScreenQuery) -> RosterManagementScreenQueryResult:
        if not self._game_repository.does_game_exist(query.game_id):
            return RosterManagementScreenQueryResult(
                success=False,
                message=f"Game with id={query.game_id} not found",
                main_roster=[],
                balance=0,
                farm_roster=[],
                farm_club_id="",
                farm_club_name="",
            )

        clubs = self._club_provider.get_clubs_for_game(query.game_id)
        manager_club = clubs.get(query.manager_club_id)
        if manager_club is None:
            return RosterManagementScreenQueryResult(
                success=False,
                message=f"Club with id={query.manager_club_id} not found",
                main_roster=[],
                balance=0,
                farm_roster=[],
                farm_club_id="",
                farm_club_name="",
            )

        farm_club = clubs.get(manager_club.farm_club_id)
        main_roster = _make_roster(
            self._player_assignment_repository.get_players_for_club(
                query.game_id,
                manager_club.club_id,
            ),
        )
        farm_roster = _make_roster(
            self._player_assignment_repository.get_players_for_club(
                query.game_id,
                farm_club.club_id,
            ) if farm_club is not None else [],
        )

        return RosterManagementScreenQueryResult(
            success=True,
            message="Ok",
            main_roster=main_roster,
            balance=manager_club.account.balance,
            farm_roster=farm_roster,
            farm_club_id="" if farm_club is None else farm_club.club_id,
            farm_club_name="" if farm_club is None else farm_club.name,
        )


def _make_roster(assigned_players):
    return [
        _player_to_roster_info(player_data, player_pos)
        for player_pos, player_data in enumerate(assigned_players)
    ]


def _player_to_roster_info(player_data, player_pos):
    player, _, contract_cost, contract_status = player_data

    return PlayerRosterInfo(
        player_id=player.player_id,
        pos=player_pos,
        name=f"{player.first_name} {player.last_name}",
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        age=player.age,
        contract_cost=None if contract_status == "future" else contract_cost,
        contract_status="Signed" if contract_status == "future" else "Not Signed",
    )
