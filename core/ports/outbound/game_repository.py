"""
Created December 26, 2025

@author montreal91
"""
import pickle
from sqlite3 import Binary
from sqlite3 import Connection
from typing import Dict
from typing import Optional

from core.game import Game
from persistence.sql import read_sql_file


class GameRepository:
    _games: Dict[str, Game]

    def __init__(self, conn: Connection):
        self._games = {}
        self._conn = conn

        self._save_game_sql = read_sql_file("data/sql/save_game.sql")
        self._get_games_sql = read_sql_file("data/sql/get_game.sql")
        self._get_game_ids_sql = read_sql_file("data/sql/get_game_ids.sql")

    def get_game(self, game_id) -> Optional[Game]:
        if game_id in self._games:
            return self._games[game_id]

        game = self._load_game(game_id)
        self._games[game_id] = game

        return game

    def does_game_exist(self, game_id: str) -> bool:
        row = self._conn.execute(
            """
            SELECT 1
            FROM game
            WHERE game_id = :game_id
            LIMIT 1
            """,
            {"game_id": game_id},
        ).fetchone()
        return row is not None

    def get_game_ids(self):
        query_res = self._conn.execute(self._get_game_ids_sql).fetchall()
        return [row[0] for row in query_res]

    def save_game(self, game: Game):
        self._games = {} # invalidate cache
        self._save_game_to_file(game)

    def _load_game(self, game_id: str) -> Game:
        res = self._conn.execute(self._get_games_sql, {"id": game_id}).fetchone()
        game = pickle.loads(res[1])
        return game

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
