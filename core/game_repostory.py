"""
Created May 11, 2024

@author montreal91
"""
import os


class GameRepository:
    _SAVE_FOLDER = ".saves"

    def __init__(self):
        self._games = {}

    def get_game(self, game_id):
        if game_id not in self._games:
            self._load_game(game_id)

        return self._games.get(game_id)

    def save_game(self, game, quitting=False):
        self._games[game.game_id] = game

        if quitting:
            self._save_game_to_file(game.game_id, game)

    def _load_game(self, game_id):
        save_path = os.path.join(self._SAVE_FOLDER, game_id)
        if os.path.isfile(save_path):
            with open(save_path, "rb") as save_file:
                slot = pickle.load(save_file)
                # self._club_pk = slot["club_pk"]
                self._games[game_id] = slot["game"]
                print(f"Game [{game_id}] is loaded successfully.")
        else:
            print(f"Game [{game_id}] does not exist.")

    def _save_game_to_file(self, game_id, game):
        save_path = os.path.join(self._SAVE_FOLDER, game_id)
        with open(save_path, "wb") as save_file:
            slot = {"club_pk": self._club_pk}
            slot["game"] = game
            pickle.dump(slot, save_file)
            print(f"The game [{game_id}] is saved.")
