"""
Created August 31, 2026

@author montreal91
"""
from sqlite3 import Row
from typing import List

from core.scheduled_match import ScheduledMatch


class ScheduledMatchRepository:
    _TMP_INSTANCE = None

    @staticmethod
    def tmp_init(conn=None):
        ScheduledMatchRepository._TMP_INSTANCE = ScheduledMatchRepository(conn)

    @staticmethod
    def tmp_get_instance() -> "ScheduledMatchRepository":
        return ScheduledMatchRepository._TMP_INSTANCE

    def __init__(self, conn=None):
        self._conn = conn
        if self._conn is not None:
            self._conn.row_factory = Row

    def save_matches(self, game_id: str, matches: List[ScheduledMatch]) -> None:
        if self._conn is None:
            raise RuntimeError("ScheduledMatchRepository has no SQLite connection.")

        with self._conn:
            for match in matches:
                self._conn.execute(
                    """
                    INSERT INTO scheduled_match (
                        game_id,
                        competition_id,
                        match_id,
                        schedule_day,
                        home_club_id,
                        away_club_id,
                        playoff_series_id,
                        is_played
                    )
                    VALUES (
                        :game_id,
                        :competition_id,
                        :match_id,
                        :schedule_day,
                        :home_club_id,
                        :away_club_id,
                        :playoff_series_id,
                        :is_played
                    )
                    ON CONFLICT(game_id, match_id) DO UPDATE SET
                        competition_id = excluded.competition_id,
                        schedule_day = excluded.schedule_day,
                        home_club_id = excluded.home_club_id,
                        away_club_id = excluded.away_club_id,
                        playoff_series_id = excluded.playoff_series_id,
                        is_played = excluded.is_played
                    """,
                    {
                        "game_id": game_id,
                        "competition_id": match.competition_id,
                        "match_id": match.match_id,
                        "schedule_day": match.schedule_day,
                        "home_club_id": match.home_pk,
                        "away_club_id": match.away_pk,
                        "playoff_series_id": match.playoff_series_id,
                        "is_played": int(match.is_played),
                    },
                )

    def get_matches_for_competition(
            self,
            game_id: str,
            competition_id: str,
            day: int,
    ) -> List[ScheduledMatch]:
        if self._conn is None:
            raise RuntimeError("ScheduledMatchRepository has no SQLite connection.")

        rows = self._conn.execute(
            """
            SELECT
                match_id,
                home_club_id,
                away_club_id,
                playoff_series_id,
                is_played
            FROM scheduled_match
            WHERE game_id = :game_id
              AND competition_id = :competition_id
              AND schedule_day = :schedule_day
              AND is_played = 0
            ORDER BY match_id
            """,
            {
                "game_id": game_id,
                "competition_id": competition_id,
                "schedule_day": day,
            },
        ).fetchall()

        matches = []
        for row in rows:
            match = ScheduledMatch(
                home_pk=row["home_club_id"],
                away_pk=row["away_club_id"],
                competition_id=competition_id,
                schedule_day=day,
                match_id=row["match_id"],
                playoff_series_id=row["playoff_series_id"],
            )
            match.is_played = bool(row["is_played"])
            matches.append(match)

        return matches
