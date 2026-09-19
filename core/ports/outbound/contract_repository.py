"""Persistence for player employment contracts."""

from sqlite3 import Connection


class ContractRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def create_active_contract(
            self,
            game_id: str,
            club_id: str,
            player_id: str,
            season_index: int,
            contract_cost: int,
    ):
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO "contract" (
                    game_id,
                    club_id,
                    player_id,
                    season_index,
                    contract_cost,
                    status
                )
                VALUES (?, ?, ?, ?, ?, 'active')
                """,
                (game_id, club_id, player_id, season_index, contract_cost),
            )
