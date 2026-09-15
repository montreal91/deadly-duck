"""
Created September 14, 2026

@author montreal91
"""
from pickle import HIGHEST_PROTOCOL
from pickle import dumps
from sqlite3 import Connection
from sqlite3 import Row
from sqlite3 import Binary
from typing import Dict
from typing import List

from core.competition import AbstractCompetition
from core.competition import CompetitionType
from core.playoffs import Playoff
from core.regular_championship import RegularChampionship


class CompetitionRepository:
    _INSTANCE = None

    _cache: Dict[str, List[AbstractCompetition]]

    @staticmethod
    def temporal_initialize(conn=None):
        CompetitionRepository._INSTANCE = CompetitionRepository(conn)

    @staticmethod
    def temporal_get_instance() -> "CompetitionRepository":
        if CompetitionRepository._INSTANCE is None:
            raise Exception("CompetitionRepository has not been initialized.")

        return CompetitionRepository._INSTANCE

    def __init__(self, conn: Connection):
        self._conn = conn
        self._cache = {}

        if self._conn is not None:
            self._conn.row_factory = Row
            self._conn.execute("PRAGMA foreign_keys = ON;")

    def get_ongoing_competitions(self, game_id: str) -> List[AbstractCompetition]:
        if game_id in self._cache:
            return self._cache[game_id]

        if self._conn is None:
            raise RuntimeError("CompetitionRepository has no SQLite connection.")

        rows = self._conn.execute(
            """
            SELECT day, object
            FROM competition
            WHERE game_id = :game_id
              AND is_over = 0
            ORDER BY season_index, day
            """,
            {"game_id": game_id},
        ).fetchall()

        res = [
            _load_competition_from_row(row)
            for row in rows
        ]
        self._cache[game_id] = res
        return res

    def get_season_competitions(self, game_id: str, season_index: int) -> List[AbstractCompetition]:
        if self._conn is None:
            raise RuntimeError("CompetitionRepository has no SQLite connection.")

        rows = self._conn.execute(
            """
            SELECT day, object
            FROM competition
            WHERE game_id = :game_id
              AND season_index = :season_index
            ORDER BY day
            """,
            {
                "game_id": game_id,
                "season_index": season_index,
            },
        ).fetchall()

        return [
            _load_competition_from_row(row)
            for row in rows
        ]

    def save_competition(
            self,
            game_id: str,
            competition: AbstractCompetition,
            season_index: int,
    ):
        if self._conn is None:
            raise RuntimeError("CompetitionRepository has no SQLite connection.")

        competition_type = _competition_type(competition)

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO competition (
                    game_id,
                    competition_id,
                    type,
                    day,
                    season_index,
                    is_over,
                    object
                )
                VALUES (
                    :game_id,
                    :competition_id,
                    :type,
                    :day,
                    :season_index,
                    :is_over,
                    :object
                )
                ON CONFLICT(game_id, competition_id) DO UPDATE SET
                    type = excluded.type,
                    day = excluded.day,
                    season_index = excluded.season_index,
                    is_over = excluded.is_over,
                    object = excluded.object
                """,
                {
                    "game_id": game_id,
                    "competition_id": competition.competition_id,
                    "type": competition_type.value,
                    "day": competition.day,
                    "season_index": season_index,
                    "is_over": int(competition.is_over),
                    "object": Binary(dumps(
                        competition,
                        HIGHEST_PROTOCOL,
                    )),
                },
            )
        self._cache = {}


def _load_competition_from_row(row) -> AbstractCompetition:
    if row["object"] is None or row["day"] is None:
        raise RuntimeError(
            "The stored object is invalid."
        )

    return AbstractCompetition.reconstruct(row["object"], row["day"])


def _competition_type(competition) -> CompetitionType:
    if isinstance(competition, RegularChampionship):
        return CompetitionType.CHAMPIONSHIP
    if isinstance(competition, Playoff):
        return CompetitionType.PLAY_OFFS
    raise Exception("Unknown competition type.")
