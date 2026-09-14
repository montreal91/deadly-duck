"""
Created September 14, 2026

@author montreal91
"""
from sqlite3 import Row

from core.competition import AbstractCompetition
from core.competition import CompetitionType
from core.playoffs import Playoff
from core.regular_championship import RegularChampionship


class CompetitionRepository:
    _INSTANCE = None

    @staticmethod
    def temporal_initialize(conn=None):
        CompetitionRepository._INSTANCE = CompetitionRepository(conn)

    @staticmethod
    def temporal_get_instance():
        if CompetitionRepository._INSTANCE is None:
            raise Exception("CompetitionRepository has not been initialized.")

        return CompetitionRepository._INSTANCE

    def __init__(self, conn=None):
        self._conn = conn

        if self._conn is not None:
            self._conn.row_factory = Row
            self._conn.execute("PRAGMA foreign_keys = ON;")

    def save(
            self,
            game_id: str,
            competition: AbstractCompetition,
            season_index: int,
            is_current: bool = True,
    ):
        if self._conn is None:
            raise RuntimeError("CompetitionRepository has no SQLite connection.")

        competition_type = _competition_type(competition)

        with self._conn:
            if is_current:
                self._conn.execute(
                    """
                    UPDATE competition
                    SET is_current = 0
                    WHERE game_id = :game_id
                    """,
                    {"game_id": game_id},
                )

            self._conn.execute(
                """
                INSERT INTO competition (
                    game_id,
                    competition_id,
                    type,
                    day,
                    season_index,
                    is_current
                )
                VALUES (
                    :game_id,
                    :competition_id,
                    :type,
                    :day,
                    :season_index,
                    :is_current
                )
                ON CONFLICT(game_id, competition_id) DO UPDATE SET
                    type = excluded.type,
                    day = excluded.day,
                    season_index = excluded.season_index,
                    is_current = excluded.is_current
                """,
                {
                    "game_id": game_id,
                    "competition_id": competition.competition_id,
                    "type": competition_type.value,
                    "day": competition.day,
                    "season_index": season_index,
                    "is_current": int(is_current),
                },
            )


def _competition_type(competition) -> CompetitionType:
    if isinstance(competition, RegularChampionship):
        return CompetitionType.CHAMPIONSHIP
    if isinstance(competition, Playoff):
        return CompetitionType.PLAY_OFFS
    raise Exception("Unknown competition type.")
