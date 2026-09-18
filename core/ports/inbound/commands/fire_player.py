"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass

from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class FirePlayerCommand:
    game_id: str
    club_id: str
    player_id: str


@dataclass(frozen=True)
class FirePlayerCommandResult:
    success: bool
    message: str


class FirePlayerCommandHandler:
    def __init__(self, game_repository: GameRepository, club_provider: TemporalClubProvider):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(self, command: FirePlayerCommand) -> FirePlayerCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return FirePlayerCommandResult(success=False, message="Game not found")

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        club = clubs.get(command.club_id)
        if club is None:
            return FirePlayerCommandResult(
                success=False,
                message="Incorrect club id.",
            )

        if not club.has_player(command.player_id):
            return FirePlayerCommandResult(
                success=False,
                message="There is no player with such id in your club.",
            )

        player = club.pop_player(command.player_id)
        player.recover_stamina(player.max_stamina)
        self._club_provider.save_club(club)

        return FirePlayerCommandResult(success=True, message="")
