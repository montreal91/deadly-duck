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
    def __init__(
            self,
            game_repository,
            game_parameters,
            club_provider,
            competition_repository=None,
    ):
        self._game_repository = game_repository
        self._parameters = game_parameters
        self._club_provider = club_provider
        self._competition_repository = competition_repository

    def __call__(self, command):
        game = Game(
            game_id=command.game_id,
            params=self._parameters,
            created_ts=time.time_ns() // 1_000_000,
            updated_ts=time.time_ns() // 1_000_000,
        )
        self._game_repository.save_game(game)
        self._club_provider.save_clubs(game.clubs.values())
        if self._competition_repository is not None:
            self._competition_repository.save(
                game_id=game.game_id,
                competition=game.competition,
                season_index=game.season_index,
            )

        return CreateNewGameCommandResult(game.game_id)
