"""
Created December 26, 2025

@author montreal91
"""


class ClubRepository:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def get_all_clubs(self, game_id):
        game = self._game_repository.get_game(game_id)

        if game is None:
            return []

        return game.clubs.values()

    def get_club_index(self, game_id):
        game = self._game_repository.get_game(game_id)
        clubs = game.clubs
        res = {}

        for club in clubs.values():
            res[club.club_id] = club

        return res
