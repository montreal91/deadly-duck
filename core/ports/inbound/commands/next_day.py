"""
Created December 30, 2025

@author montreal91
"""
from typing import NamedTuple


class NextDayCommand(NamedTuple):
    game_id: str


class NextDayCommandResult(NamedTuple):
    success: bool
    reason: str


class NextDayCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, command):
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return NextDayCommandResult(
                success=False,
                reason=f"Game with id={command.game_id} not found"
            )

        res, reason = game.update()
        self._game_repository.save_game(game)
        return NextDayCommandResult(success=res, reason=reason)
