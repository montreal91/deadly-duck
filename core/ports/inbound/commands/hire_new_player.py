"""
Created August 17, 2026

@author montreal91
"""
from typing import NamedTuple


class HireNewPlayerCommand(NamedTuple):
    club_id: str
    game_id: str


class HireNewPlayerCommandResult(NamedTuple):
    success: bool


class HireNewPlayerCommandHandler:
    def __init__(self, game_repository, club_provider):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(self, command: HireNewPlayerCommand) -> HireNewPlayerCommandResult:
        game = self._game_repository.get_game(command.game_id)
        game.hire_new_player(command.club_id)
        self._game_repository.save_game(game)
        self._club_provider.save_clubs(game.clubs.values())

        return HireNewPlayerCommandResult(success=True)
