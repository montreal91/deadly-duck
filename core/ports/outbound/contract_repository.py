"""
Created September 19, 2026

@author montreal91

Persistence for player employment contracts.
"""

from sqlite3 import Connection

from core.contract import Contract


class ContractRepository:
    _TMP_INSTANCE = None

    @staticmethod
    def tmp_init(conn: Connection):
        ContractRepository._TMP_INSTANCE = ContractRepository(conn)

    @staticmethod
    def tmp_get_instance():
        return ContractRepository._TMP_INSTANCE

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
        self.save_contract(Contract(
            game_id, club_id, player_id, season_index, contract_cost, "active",
        ))

    def save_contract(self, contract: Contract):
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
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    contract.game_id,
                    contract.club_id,
                    contract.player_id,
                    contract.season_index,
                    contract.contract_cost,
                    contract.status,
                ),
            )

    def create_future_contract(
            self,
            game_id: str,
            club_id: str,
            player_id: str,
            season_index: int,
            contract_cost: int,
    ):
        self.save_contract(Contract(
            game_id, club_id, player_id, season_index, contract_cost, "future",
        ))

    def has_future_contract(self, game_id: str, player_id: str) -> bool:
        return self._conn.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM "contract"
                WHERE game_id = ?
                  AND player_id = ?
                  AND status = 'future'
            )
            """,
            (game_id, player_id),
        ).fetchone()[0] == 1
