"""
Created September 14, 2026

@author montreal91
"""
from sqlite3 import Row
from sqlite3 import Binary
import pickle
from typing import Dict
from typing import List

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
        self._ongoing_competitions: Dict[str, AbstractCompetition] = {}

        if self._conn is not None:
            self._conn.row_factory = Row
            self._conn.execute("PRAGMA foreign_keys = ON;")

    def get_ongoing_competitions(self) -> List[AbstractCompetition]:
        if self._conn is None:
            return list(self._ongoing_competitions.values())

        rows = self._conn.execute(
            """
            SELECT game_id, object
            FROM competition
            WHERE is_over = 0
            ORDER BY game_id, season_index, day
            """
        ).fetchall()

        competitions = []
        for row in rows:
            competition = self._load_competition_from_row(row)
            competitions.append(competition)
            self._ongoing_competitions[row["game_id"]] = competition

        return competitions

    def get_current_competition(self, game_id: str) -> AbstractCompetition:
        if game_id in self._ongoing_competitions:
            return self._ongoing_competitions[game_id]

        if self._conn is None:
            raise RuntimeError(f"No ongoing competition for game_id={game_id}.")

        row = self._conn.execute(
            """
            SELECT game_id, object
            FROM competition
            WHERE game_id = :game_id
              AND is_over = 0
            """,
            {"game_id": game_id},
        ).fetchone()

        if row is None:
            raise RuntimeError(f"No ongoing competition for game_id={game_id}.")

        competition = self._load_competition_from_row(row)
        self._ongoing_competitions[game_id] = competition
        return competition

    def set_current_competition(
            self,
            game_id: str,
            competition: AbstractCompetition,
    ):
        self._ongoing_competitions[game_id] = competition

    def save(
            self,
            game_id: str,
            competition: AbstractCompetition,
            season_index: int,
            is_over: bool = False,
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
                    "is_over": int(is_over),
                    "object": Binary(pickle.dumps(
                        competition,
                        pickle.HIGHEST_PROTOCOL,
                    )),
                },
            )

        if not is_over:
            self._ongoing_competitions[game_id] = competition
        elif self._ongoing_competitions.get(game_id) is competition:
            del self._ongoing_competitions[game_id]

    @staticmethod
    def _load_competition_from_row(row) -> AbstractCompetition:
        if row["object"] is None:
            raise RuntimeError(
                "Ongoing competition row has no serialized object."
            )

        return pickle.loads(row["object"])


def _competition_type(competition) -> CompetitionType:
    if isinstance(competition, RegularChampionship):
        return CompetitionType.CHAMPIONSHIP
    if isinstance(competition, Playoff):
        return CompetitionType.PLAY_OFFS
    raise Exception("Unknown competition type.")
