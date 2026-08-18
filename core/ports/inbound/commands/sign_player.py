"""
Created August 17, 2026

@author montreal91
"""
from typing import NamedTuple
from uuid import UUID


class SignPlayerCommand(NamedTuple):
    game_id: str
    club_id: UUID
    player_id: str


class SignPlayerCommandResult(NamedTuple):
    success: bool
    message: str


class SignPlayerCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, command: SignPlayerCommand) -> SignPlayerCommandResult:
        game = self._game_repository.get_game(command.game_id)
        success, message = game.sign_player(
            club_id=command.club_id,
            player_id=command.player_id,
        )
        self._game_repository.save_game(game)

        return SignPlayerCommandResult(success=success, message=message)
