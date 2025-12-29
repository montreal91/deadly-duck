"""
Created December 29, 2025

@author montreal91
"""
import time
from typing import NamedTuple

from core.game import Game


class CreateNewGameCommand(NamedTuple):
    game_id: str


class CreateNewGameCommandResult(NamedTuple):
    game_id: str


class CreateNewGameCommandHandler:
    def __init__(self, game_repository, game_parameters):
        self._game_repository = game_repository
        self._parameters = game_parameters

    def __call__(self, command):
        game = Game(
            game_id=command.game_id,
            params=self._parameters,
            created_ts=time.time_ns() // 1_000_000,
            updated_ts=time.time_ns() // 1_000_000,
        )
        self._game_repository.save_game(game)

        return CreateNewGameCommandResult(game.game_id)
