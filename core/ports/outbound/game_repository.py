import pickle
from sqlite3 import Binary
from time import time_ns

from core.game import Game
from persistence.sql import read_sql_file


class GameRepository:
    def __init__(self, conn):
        self._games = {}
        self._conn = conn

        self._save_game_sql = read_sql_file("data/sql/save_game.sql")
        self._get_games_sql = read_sql_file("data/sql/get_game.sql")
        self._get_game_ids_sql = read_sql_file("data/sql/get_game_ids.sql")

    def get_game(self, game_id) -> Game:
        if game_id not in self._games:
            self._load_game(game_id)

        return self._games.get(game_id)

    def get_game_ids(self):
        query_res = self._conn.execute(self._get_game_ids_sql).fetchall()
        return [row[0] for row in query_res]


    #
    #     def get_game_ids(self):
    #         folder = Path(self._SAVE_FOLDER)
    #         games = [p.name for p in folder.iterdir() if p.is_file()]
    #         return games
    #
    def save_game(self, game, persistent_save=False):
        self._games[game.game_id] = game

        if persistent_save:
            self._save_game_to_file(game)

    def _load_game(self, game_id):
        res = self._conn.execute(self._get_games_sql, {"id": game_id}).fetchone()
        # print(res)
        # print(dir(res))
        game = pickle.loads(res[1])
        self._games[game_id] = game

    #     def _load_game(self, game_id):
    #         if game_id is None:
    #             print("No game id provided.")
    #             return
    #
    #         save_path = os.path.join(self._SAVE_FOLDER, game_id)
    #         if os.path.isfile(save_path):
    #             with open(save_path, "rb") as save_file:
    #                 game = pickle.load(save_file)
    #                 self._games[game_id] = game
    #                 print(f"Game [{game_id}] is loaded successfully.")
    #         else:
    #             print(f"Game [{game_id}] does not exist.")
    #
    def _save_game_to_file(self, game: Game):
        blob = pickle.dumps(game, pickle.HIGHEST_PROTOCOL)

        args = {
            "blob": Binary(blob),
            "id": game.game_id,
            "created_ts": game.created_ts,
            "updated_ts": game.updated_ts,
        }

        self._conn.execute(self._save_game_sql, args)
        self._conn.commit()
