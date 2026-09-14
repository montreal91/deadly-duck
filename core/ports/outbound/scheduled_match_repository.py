"""
Created August 31, 2026

@author montreal91
"""
from typing import List

from core.scheduled_match import ScheduledMatch


class ScheduledMatchRepository:
    def __init__(self, conn=None):
        self._conn = conn

    def save_matches(self, game_id: str, matches: List[ScheduledMatch]) -> None:
        if self._conn is None:
            raise RuntimeError("ScheduledMatchRepository has no SQLite connection.")

        positions = {}

        with self._conn:
            for match in matches:
                position_key = (match.competition_id, match.schedule_day)
                position = positions.get(position_key, 0)
                positions[position_key] = position + 1

                self._conn.execute(
                    """
                    INSERT INTO scheduled_match (
                        game_id,
                        competition_id,
                        match_id,
                        schedule_day,
                        position,
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
                        :position,
                        :home_club_id,
                        :away_club_id,
                        :playoff_series_id,
                        :is_played
                    )
                    ON CONFLICT(game_id, match_id) DO UPDATE SET
                        competition_id = excluded.competition_id,
                        schedule_day = excluded.schedule_day,
                        position = excluded.position,
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
                        "position": position,
                        "home_club_id": match.home_pk,
                        "away_club_id": match.away_pk,
                        "playoff_series_id": match.playoff_series_id,
                        "is_played": int(match.is_played),
                    },
                )
