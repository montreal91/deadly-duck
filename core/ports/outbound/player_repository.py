"""
Created August 20, 2026

@author montreal91
"""
from sqlite3 import Row
from typing import NamedTuple
from typing import Optional

from core.player import Player


class PlayerRecord(NamedTuple):
    game_id: str
    player_id: str
    first_name: str
    second_name: str
    last_name: str
    age: int
    technique: int
    endurance: int
    exhaustion: int
    experience: int
    current_stamina: int
    reputation: int
    club_id: Optional[str]
    club_name: Optional[str]
    coach_level: Optional[int]
    contract_cost: Optional[int]
    has_next_contract: Optional[bool]

    @property
    def player(self) -> Player:
        player = Player(
            first_name=self.first_name,
            second_name=self.second_name,
            last_name=self.last_name,
            technique=self.technique,
            endurance=self.endurance,
            age=self.age,
        )
        player._player_id = self.player_id
        player._exhaustion = self.exhaustion
        player._experience = self.experience
        player._current_stamina = self.current_stamina
        player._reputation = self.reputation
        return player


class PlayerRepository:
    def __init__(self, conn):
        self._conn = conn
        self._conn.row_factory = Row

    def get_player(
            self,
            game_id: str,
            player_id: str,
    ) -> Optional[PlayerRecord]:
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
                player.current_stamina,
                player.reputation,
                roster_entry.club_id,
                club.name AS club_name,
                roster_entry.coach_level,
                roster_entry.contract_cost,
                roster_entry.has_next_contract
            FROM player
            LEFT JOIN roster_entry
              ON roster_entry.game_id = player.game_id
             AND roster_entry.player_id = player.player_id
            LEFT JOIN club
              ON club.game_id = roster_entry.game_id
             AND club.club_id = roster_entry.club_id
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

        return PlayerRecord(
            game_id=row["game_id"],
            player_id=row["player_id"],
            first_name=row["first_name"],
            second_name=row["second_name"],
            last_name=row["last_name"],
            age=row["age"],
            technique=row["technique"],
            endurance=row["endurance"],
            exhaustion=row["exhaustion"],
            experience=row["experience"],
            current_stamina=row["current_stamina"],
            reputation=row["reputation"],
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
