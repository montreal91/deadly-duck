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
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return FirePlayerCommandResult(success=False, message="Game not found")

        game.fire_player(club_id=command.club_id, player_id=command.player_id)
        self._game_repository.save_game(game)
        self._club_provider.save_clubs(game.clubs.values())

        return FirePlayerCommandResult(success=True, message="")
