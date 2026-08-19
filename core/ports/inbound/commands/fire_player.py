"""
Created August 17, 2026

@author montreal91
"""
from typing import NamedTuple


class FirePlayerCommand(NamedTuple):
    game_id: str
    club_id: str
    player_id: str


class FirePlayerCommandResult(NamedTuple):
    success: bool
    message: str


class FirePlayerCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, command: FirePlayerCommand) -> FirePlayerCommandResult:
        game = self._game_repository.get_game(command.game_id)
        game.fire_player(club_id=command.club_id, player_id=command.player_id)
        self._game_repository.save_game(game)

        return FirePlayerCommandResult(success=True, message="")
