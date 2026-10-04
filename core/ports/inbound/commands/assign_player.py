"""
Created September 19, 2026

@author montreal91
"""

from dataclasses import dataclass

from core.ports.outbound.player_assignment_repository import (
    PlayerAssignmentRepository,
)
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_MASTER_LEAGUE_ID = "master_league"
_INVALID_ASSIGNMENT_ERROR = "Player cannot be assigned to this club."

@dataclass(frozen=True)
class AssignPlayerCommand:
    game_id: str
    master_club_id: str
    target_club_id: str
    player_id: str


@dataclass(frozen=True)
class AssignPlayerCommandResult:
    success: bool
    message: str = ""


class AssignPlayerCommandHandler:
    def __init__(
            self,
            club_provider: TemporalClubProvider,
            player_assignment_repository: PlayerAssignmentRepository
    ):
        self._club_provider = club_provider
        self._player_assignment_repository = player_assignment_repository

    def __call__(self, command: AssignPlayerCommand) -> AssignPlayerCommandResult:
        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        master_club = clubs.get(command.master_club_id)
        target_club = clubs.get(command.target_club_id)
        current_club_id = self._player_assignment_repository.get_assigned_club_id(
            command.game_id,
            command.player_id,
        )

        if (
                master_club is None
                or master_club.league_id != _MASTER_LEAGUE_ID
                or target_club is None
                or command.target_club_id not in {
                    master_club.club_id,
                    master_club.farm_club_id,
                }
                or current_club_id not in {
                    master_club.club_id,
                    master_club.farm_club_id,
                }
                or current_club_id == command.target_club_id
        ):
            return AssignPlayerCommandResult(False, _INVALID_ASSIGNMENT_ERROR)

        self._player_assignment_repository.assign_player(
            game_id=command.game_id,
            club_id=command.target_club_id,
            player_id=command.player_id,
        )
        return AssignPlayerCommandResult(True)
