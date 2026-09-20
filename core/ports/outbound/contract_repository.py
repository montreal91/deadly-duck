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

    def create_future_contract(
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
                VALUES (?, ?, ?, ?, ?, 'future')
                """,
                (game_id, club_id, player_id, season_index, contract_cost),
            )

    def has_future_contract(self, game_id: str, player_id: str) -> bool:
        return self._conn.execute(
            '''
            SELECT EXISTS(
                SELECT 1
                FROM "contract"
                WHERE game_id = ?
                  AND player_id = ?
                  AND status = 'future'
            )
            ''',
            (game_id, player_id),
        ).fetchone()[0] == 1
