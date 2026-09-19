"""Persistence for a player's current club assignment."""

from sqlite3 import Connection
from typing import Optional


class PlayerAssignmentRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def assign_player(
            self,
            game_id: str,
            club_id: str,
            player_id: str,
            coach_level: int = 0,
    ):
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO player_assignment (
                    game_id,
                    club_id,
                    player_id,
                    coach_level
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(game_id, player_id) DO UPDATE SET
                    club_id = excluded.club_id,
                    coach_level = excluded.coach_level
                """,
                (game_id, club_id, player_id, coach_level),
            )

    def get_assigned_club_id(
            self,
            game_id: str,
            player_id: str,
    ) -> Optional[str]:
        row = self._conn.execute(
            """
            SELECT club_id
            FROM player_assignment
            WHERE game_id = ? AND player_id = ?
            """,
            (game_id, player_id),
        ).fetchone()
        return None if row is None else row[0]
