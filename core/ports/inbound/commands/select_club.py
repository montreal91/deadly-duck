"""
Created December 30, 2025

@author montreal91
"""
from typing import NamedTuple

from core.ports.outbound.game_repository import GameRepository


class SelectClubCommand(NamedTuple):
    club_id: str
    game_id: str


class SelectClubCommandResult(NamedTuple):
    success: bool


class SelectClubCommandHandler:
    def __init__(self, game_repository: GameRepository):
        self._game_repository = game_repository

    def __call__(self, query):
        game = self._game_repository.get_game(query.game_id)

        if game is None:
            return SelectClubCommandResult(success=False)

        game.set_managed(query.club_id, True)
        self._game_repository.save_game(game)

        return SelectClubCommandResult(success=True)
