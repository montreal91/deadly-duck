"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass

from core.club import Club
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class SelectCoachForPlayerCommand:
    game_id: str
    club_id: str
    player_id: str
    coach_index: int


@dataclass(frozen=True)
class SelectCoachForPlayerCommandResult:
    success: bool
    message: str


class SelectCoachForPlayerCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider: TemporalClubProvider
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(
            self,
            command: SelectCoachForPlayerCommand
    ) -> SelectCoachForPlayerCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return SelectCoachForPlayerCommandResult(
                success=False,
                message=f"Game with id={command.game_id} not found",
            )

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        club = clubs.get(command.club_id)
        if club is None:
            return SelectCoachForPlayerCommandResult(
                success=False,
                message="Incorrect club id.",
            )

        if not club.has_player(command.player_id):
            return SelectCoachForPlayerCommandResult(
                success=False,
                message="Incorrect player index.",
            )

        if command.coach_index not in range(len(Club.COACH_LEVELS)):
            return SelectCoachForPlayerCommandResult(
                success=False,
                message="Incorrect coach index.",
            )

        club.select_coach(
            coach_index=command.coach_index,
            player_id=command.player_id,
        )
        self._club_provider.save_club(club)

        return SelectCoachForPlayerCommandResult(success=True, message="")
