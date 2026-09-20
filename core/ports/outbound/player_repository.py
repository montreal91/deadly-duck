"""
Created August 20, 2026

@author montreal91
"""
from dataclasses import dataclass
from sqlite3 import Connection
from sqlite3 import Row
from typing import List
from typing import Optional

from core.player import Player
from core.ports.outbound.player_mapper import make_player_from_row


@dataclass(frozen=True)
class PlayerRosterInfo:
    player: Player
    club_id: Optional[str]
    club_name: Optional[str]
    coach_level: Optional[int]
    contract_cost: Optional[int]
    has_next_contract: Optional[bool]


class PlayerRepository:
    _TMP_INSTANCE = None

    @staticmethod
    def tmp_init(conn: Connection):
        PlayerRepository._TMP_INSTANCE = PlayerRepository(conn)

    @staticmethod
    def tmp_get_instance() -> "PlayerRepository":
        return PlayerRepository._TMP_INSTANCE

    def __init__(self, conn: Connection):
        self._conn = conn
        self._conn.row_factory = Row

    def save_player(self, player: Player):
        with self._conn:
            self._conn.execute(
                """
                UPDATE player
                SET first_name = :first_name,
                    second_name = :second_name,
                    last_name = :last_name,
                    age = :age,
                    technique = :technique,
                    endurance = :endurance,
                    exhaustion = :exhaustion,
                    experience = :experience,
                    skill_points = :skill_points,
                    current_stamina = :current_stamina,
                    reputation = :reputation
                WHERE player_id = :player_id
                """,
                _player_params(player),
            )

    def get_player(
            self,
            game_id: str,
            player_id: str,
    ) -> Optional[Player]:
        row = self._conn.execute(
            """
            SELECT
                game_id,
                player_id,
                first_name,
                second_name,
                last_name,
                age,
                technique,
                endurance,
                exhaustion,
                experience,
                skill_points,
                current_stamina,
                reputation
            FROM player
            WHERE game_id = :game_id
              AND player_id = :player_id
            """,
            {
                "game_id": game_id,
                "player_id": player_id,
            },
        ).fetchone()

        if row is None:
            return None

        return make_player_from_row(row)

    def get_all_active_players(self, game_id: str, max_age: int) -> List[Player]:
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
                player.reputation
            FROM player
            JOIN roster_entry
              ON roster_entry.game_id = player.game_id
             AND roster_entry.player_id = player.player_id
            WHERE player.game_id = :game_id
              AND player.age < :max_age
            ORDER BY player.player_id
            """,
            {
                "game_id": game_id,
                "max_age": max_age,
            },
        ).fetchall()

        return [
            make_player_from_row(row)
            for row in rows
        ]

    def get_player_with_roster_info(
            self,
            game_id: str,
            player_id: str,
    ) -> Optional[PlayerRosterInfo]:
        row = self._conn.execute(
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
                roster_entry.club_id,
                club.name AS club_name,
                roster_entry.coach_level,
                roster_entry.contract_cost,
                CASE
                    WHEN future_contract.player_id IS NULL THEN 0
                    ELSE 1
                END AS has_next_contract
            FROM player
            LEFT JOIN roster_entry
              ON roster_entry.game_id = player.game_id
             AND roster_entry.player_id = player.player_id
            LEFT JOIN club
              ON club.game_id = roster_entry.game_id
             AND club.club_id = roster_entry.club_id
            LEFT JOIN "contract" AS future_contract
              ON future_contract.game_id = player.game_id
             AND future_contract.player_id = player.player_id
             AND future_contract.club_id = roster_entry.club_id
             AND future_contract.status = 'future'
            WHERE player.game_id = :game_id
              AND player.player_id = :player_id
            """,
            {
                "game_id": game_id,
                "player_id": player_id,
            },
        ).fetchone()

        if row is None:
            return None

        return PlayerRosterInfo(
            player=make_player_from_row(row),
            club_id=row["club_id"],
            club_name=row["club_name"],
            coach_level=row["coach_level"],
            contract_cost=row["contract_cost"],
            has_next_contract=(
                None
                if row["has_next_contract"] is None
                else bool(row["has_next_contract"])
            ),
        )


def _player_params(player: Player):
    return {
        "player_id": player.player_id,
        "first_name": player.first_name,
        "second_name": player.second_name,
        "last_name": player.last_name,
        "age": player.age,
        "technique": player.technique,
        "endurance": player.endurance,
        "exhaustion": player.exhaustion,
        "experience": player.experience,
        "skill_points": player.skill_points,
        "current_stamina": player.current_stamina,
        "reputation": player.reputation,
    }
