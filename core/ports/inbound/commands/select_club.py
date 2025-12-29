"""
Created December 30, 2025

@author montreal91
"""
from typing import NamedTuple
from uuid import UUID


class SelectClubCommand(NamedTuple):
    club_id: UUID
    game_id: str


class SelectClubCommandResult(NamedTuple):
    success: bool


class SelectClubCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, query):
        game = self._game_repository.get_game(query.game_id)

        if game is None:
            return SelectClubCommandResult(success=False)

        game.set_managed(query.club_id, True)
        self._game_repository.save_game(game, True)
        return SelectClubCommandResult(success=True)
