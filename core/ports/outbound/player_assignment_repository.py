"""Persistence for a player's current club assignment."""

from sqlite3 import Connection
from typing import Optional

from core.ports.outbound.player_mapper import make_player_from_row


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

    def get_players_for_club(self, game_id: str, club_id: str):
        rows = self._conn.execute(
            """
            SELECT
                player.game_id,
                player.player_id,
                player.first_name,
                player.second_name,
                player.last_name,
                player.age,
                player.technique,
                player.endurance,
                player.exhaustion,
                player.experience,
                player.skill_points,
                player.current_stamina,
                player.reputation,
                player_assignment.coach_level,
                next_contract.contract_cost,
                next_contract.status AS contract_status
            FROM player_assignment
            JOIN player
              ON player.game_id = player_assignment.game_id
             AND player.player_id = player_assignment.player_id
            LEFT JOIN "contract" AS next_contract
              ON next_contract.game_id = player_assignment.game_id
             AND next_contract.player_id = player_assignment.player_id
             AND next_contract.club_id = player_assignment.club_id
             AND next_contract.status = 'future'
            WHERE player_assignment.game_id = ?
              AND player_assignment.club_id = ?
            ORDER BY
                player.experience DESC,
                player.first_name,
                player.last_name
            """,
            (game_id, club_id),
        ).fetchall()
        return [
            (
                make_player_from_row(row),
                row["coach_level"],
                row["contract_cost"],
                row["contract_status"],
            )
            for row in rows
        ]
