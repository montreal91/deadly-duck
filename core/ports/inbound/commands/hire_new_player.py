"""
Created August 17, 2026

@author montreal91
"""
from typing import NamedTuple
from uuid import UUID


class HireNewPlayerCommand(NamedTuple):
    club_id: UUID
    game_id: str


class HireNewPlayerCommandResult(NamedTuple):
    success: bool


class HireNewPlayerCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, query: HireNewPlayerCommand) -> HireNewPlayerCommandResult:
        game = self._game_repository.get_game(query.game_id)
        game.hire_new_player("hard", query.club_id)
        self._game_repository.save_game(game)

        return HireNewPlayerCommandResult(success=True)
