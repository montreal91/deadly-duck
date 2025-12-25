"""
Created December 26, 2025

@author montreal91
"""
from typing import List

from core.club import Club
from core.game_repository import GameRepository


class ClubRepository:
    # TODO: get rid of this smelly stuff
    _game_repository: GameRepository

    def __init__(self, game_repository: GameRepository):
        self._game_repository = game_repository

    def get_all_clubs(self, game_id) -> List[Club]:
        game = self._game_repository.get_game(game_id)

        if game is None:
            return []

        return game.clubs

    def get_club_index(self, game_id):
        game = self._game_repository.get_game(game_id)
        clubs = game.clubs
        res = {}

        for club in clubs:
            res[club.club_id] = club

        return res
