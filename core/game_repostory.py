"""
Created May 11, 2024

@author montreal91
"""
import os
import pickle
from pathlib import Path

from core.game import Game


class GameRepository:
    _SAVE_FOLDER = ".saves"

    def __init__(self):
        self._games = {}

    def get_game(self, game_id) -> Game:
        if game_id not in self._games:
            self._load_game(game_id)

        return self._games.get(game_id)

    def get_game_ids(self):
        folder = Path(self._SAVE_FOLDER)
        games = [p.name for p in folder.iterdir() if p.is_file()]
        return games

    def save_game(self, game, persistent_save=False):
        self._games[game.game_id] = game

        if persistent_save:
            self._save_game_to_file(game.game_id, game)

    def _load_game(self, game_id):
        if game_id is None:
            print("No game id provided.")
            return

        save_path = os.path.join(self._SAVE_FOLDER, game_id)
        if os.path.isfile(save_path):
            with open(save_path, "rb") as save_file:
                game = pickle.load(save_file)
                self._games[game_id] = game
                print(f"Game [{game_id}] is loaded successfully.")
        else:
            print(f"Game [{game_id}] does not exist.")

    def _save_game_to_file(self, game_id: str, game: Game):
        save_path = os.path.join(self._SAVE_FOLDER, game_id)
        with open(save_path, "wb") as save_file:
            pickle.dump(game, save_file)
            print(f"The game [{game_id}] is saved.")
