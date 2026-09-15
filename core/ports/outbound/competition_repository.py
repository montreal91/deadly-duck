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
from core.playoffs import PlayoffSeries
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
            SELECT competition_id, type, day, object
            FROM competition
            WHERE game_id = :game_id
              AND is_over = 0
            ORDER BY season_index, day
            """,
            {"game_id": game_id},
        ).fetchall()

        res = [
            self._load_competition_from_row(game_id, row)
            for row in rows
        ]
        self._cache[game_id] = res
        return res

    def get_season_competitions(self, game_id: str, season_index: int) -> List[AbstractCompetition]:
        if self._conn is None:
            raise RuntimeError("CompetitionRepository has no SQLite connection.")

        rows = self._conn.execute(
            """
            SELECT competition_id, type, day, object
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
            self._load_competition_from_row(game_id, row)
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
            if isinstance(competition, Playoff):
                self._save_playoff_series(game_id, competition)
        self._cache = {}

    def _load_competition_from_row(
            self,
            game_id: str,
            row: Row,
    ) -> AbstractCompetition:
        competition = _load_competition_from_row(row)

        if isinstance(competition, Playoff):
            self._load_playoff_series(game_id, competition)

        return competition

    def _save_playoff_series(self, game_id: str, playoff: Playoff):
        self._conn.execute(
            """
            DELETE FROM playoff_series
            WHERE game_id = :game_id
              AND competition_id = :competition_id
            """,
            {
                "game_id": game_id,
                "competition_id": playoff.competition_id,
            },
        )

        positions = {}
        for series in playoff.series:
            position_key = series.round_number
            position = positions.get(position_key, 0)
            positions[position_key] = position + 1
            top_club_id, bottom_club_id = series.pair

            self._conn.execute(
                """
                INSERT INTO playoff_series (
                    game_id,
                    competition_id,
                    series_id,
                    round_number,
                    position,
                    top_club_id,
                    bottom_club_id
                )
                VALUES (
                    :game_id,
                    :competition_id,
                    :series_id,
                    :round_number,
                    :position,
                    :top_club_id,
                    :bottom_club_id
                )
                """,
                {
                    "game_id": game_id,
                    "competition_id": playoff.competition_id,
                    "series_id": series.series_id,
                    "round_number": series.round_number,
                    "position": position,
                    "top_club_id": top_club_id,
                    "bottom_club_id": bottom_club_id,
                },
            )

    def _load_playoff_series(self, game_id: str, playoff: Playoff):
        original_series_by_id = {
            series.series_id: series
            for series in playoff.series
        }
        rows = self._conn.execute(
            """
            SELECT
                series_id,
                round_number,
                top_club_id,
                bottom_club_id
            FROM playoff_series
            WHERE game_id = :game_id
              AND competition_id = :competition_id
            ORDER BY round_number, position
            """,
            {
                "game_id": game_id,
                "competition_id": playoff.competition_id,
            },
        ).fetchall()

        if not rows:
            return

        series = []
        for row in rows:
            loaded_series = PlayoffSeries(
                params=playoff.params,
                series_id=row["series_id"],
                round_number=row["round_number"],
            )
            loaded_series.pair = (
                row["top_club_id"],
                row["bottom_club_id"],
            )
            if loaded_series.series_id in original_series_by_id:
                loaded_series._results = original_series_by_id[
                    loaded_series.series_id
                ]._results
            series.append(loaded_series)

        playoff._past_series = [
            item
            for item in series
            if item.round_number < playoff.current_round
        ]
        playoff._series = [
            item
            for item in series
            if item.round_number == playoff.current_round
        ]
        playoff._series_by_id = {
            item.series_id: item
            for item in series
        }


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
