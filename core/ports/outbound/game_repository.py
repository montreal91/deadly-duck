"""
Created December 26, 2025

@author montreal91
"""
import pickle
from sqlite3 import Binary
from typing import Dict, Optional

from core.game import Game
from persistence.sql import read_sql_file


class GameRepository:
    _games: Dict[str, Game]

    def __init__(self, conn):
        self._games = {}
        self._conn = conn

        self._save_game_sql = read_sql_file("data/sql/save_game.sql")
        self._get_games_sql = read_sql_file("data/sql/get_game.sql")
        self._get_game_ids_sql = read_sql_file("data/sql/get_game_ids.sql")

    def get_game(self, game_id) -> Optional[Game]:
        if game_id not in self._games:
            self._load_game(game_id)

        return self._games.get(game_id)

    def get_game_ids(self):
        query_res = self._conn.execute(self._get_game_ids_sql).fetchall()
        return [row[0] for row in query_res]

    def save_game(self, game):
        self._games[game.game_id] = game
        self._save_game_to_file(game)

    def _load_game(self, game_id):
        res = self._conn.execute(self._get_games_sql, {"id": game_id}).fetchone()
        game = pickle.loads(res[1])
        game.rebind_clubs_to_provider()
        self._games[game_id] = game

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
