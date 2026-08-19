"""
Created August 19, 2026

@author montreal91
"""
import json
from sqlite3 import Row
from typing import Dict
from typing import Any
from typing import Iterable

from core.club import Club
from core.club import ClubPlayerSlot
from core.financial import DdTransaction
from core.player import Player
from core.serialization import DdJsonDecoder


class TemporalClubProvider:
    _INSTANCE = None

    _clubs: Dict[str, Dict[str, Club]]

    @staticmethod
    def initialize(conn=None):
        TemporalClubProvider._INSTANCE = TemporalClubProvider(conn)

    @staticmethod
    def get_instance() -> "TemporalClubProvider": # LOL
        if TemporalClubProvider._INSTANCE is None:
            raise Exception("TemporalClubProvider has not been initialized.")

        return TemporalClubProvider._INSTANCE

    def __init__(self, conn=None):
        self._clubs = {}
        self._conn = conn

        if self._conn is not None:
            self._conn.row_factory = Row
            self._conn.execute("PRAGMA foreign_keys = ON;")

    def init_clubs_for_game(self, game_id: str):
        self._clubs[game_id] = {}

        decoder = DdJsonDecoder()
        decoder.register(Player)
        decoder.register(ClubPlayerSlot)

        with open("data/clubs.json", "r") as data_file:
            club_data = json.load(data_file, object_hook=decoder)

        for club in club_data:
            self._add_club(game_id=game_id, club_data=club)

    def _add_club(self, game_id: str, club_data: Dict[str, Any]):
        club = Club(
            club_id=club_data["club_id"],
            game_id=game_id,
            name=club_data["name"],
            coach_power=club_data["coach_power"],
        )

        for value in club_data["fame"]:
            club.add_fame(value)

        for slot in club_data["player_data"]:
            club.add_player(slot.player)
            if slot.has_next_contract:
                club.contract_player(player_id=slot.player.player_id)

        club.account.ProcessTransaction(DdTransaction(
            club_data["balance"],
            "Initial balance",
        ))

        self._clubs[game_id][club.club_id] = club

    def save_clubs(self, clubs: Iterable[Club]):
        clubs = list(clubs)
        if not clubs:
            return

        if self._conn is None:
            raise RuntimeError("TemporalClubProvider has no SQLite connection.")

        with self._conn:
            for club in clubs:
                self._save_club(club, delete_existing_roster=True)

    def save_club(self, club: Club):
        if self._conn is None:
            raise RuntimeError("TemporalClubProvider has no SQLite connection.")

        with self._conn:
            self._save_club(club, delete_existing_roster=True)

    def get_clubs_for_game(self, game_id: str) -> Dict[str, Club]:
        if game_id not in self._clubs:
            self._load_clubs_for_game(game_id)

        return self._clubs[game_id]

    def _load_clubs_for_game(self, game_id: str):
        self._clubs[game_id] = {}

        if self._conn is None:
            return

        players = self._load_players_for_game(game_id)
        club_rows = self._conn.execute(
            """
            SELECT *
            FROM club
            WHERE game_id = :game_id
            ORDER BY name
            """,
            {"game_id": game_id},
        ).fetchall()

        for club_row in club_rows:
            club = Club(
                club_id=club_row["club_id"],
                game_id=club_row["game_id"],
                name=club_row["name"],
                coach_power=club_row["coach_power"],
            )
            club.account.ProcessTransaction(DdTransaction(
                club_row["balance"],
                "Loaded balance",
            ))

            roster_rows = self._conn.execute(
                """
                SELECT *
                FROM roster_entry
                WHERE game_id = :game_id
                  AND club_id = :club_id
                ORDER BY rowid
                """,
                {
                    "game_id": game_id,
                    "club_id": club.club_id,
                },
            ).fetchall()

            for roster_row in roster_rows:
                player = players.get(roster_row["player_id"])
                if player is None:
                    continue

                club.add_player(player)
                slot = club.get_player_slot(player.player_id)
                slot.coach_level = roster_row["coach_level"]
                slot.contract_cost = roster_row["contract_cost"]
                slot.has_next_contract = bool(roster_row["has_next_contract"])

            club.select_player(club_row["selected_player_id"])
            self._clubs[game_id][club.club_id] = club

    def _load_players_for_game(self, game_id: str) -> Dict[str, Player]:
        rows = self._conn.execute(
            """
            SELECT *
            FROM player
            WHERE game_id = :game_id
            """,
            {"game_id": game_id},
        ).fetchall()

        players = {}
        for row in rows:
            player = Player(
                first_name=row["first_name"],
                second_name=row["second_name"],
                last_name=row["last_name"],
                technique=row["technique"],
                endurance=row["endurance"],
                age=row["age"],
            )
            player._player_id = row["player_id"]
            player._exhaustion = row["exhaustion"]
            player._experience = row["experience"]
            player._current_stamina = row["current_stamina"]
            player._reputation = row["reputation"]
            players[player.player_id] = player

        return players

    def _save_club(self, club: Club, delete_existing_roster: bool):
        if delete_existing_roster:
            self._conn.execute(
                """
                DELETE FROM roster_entry
                WHERE game_id = :game_id
                  AND club_id = :club_id
                """,
                {
                     "game_id": club.game_id,
                    "club_id": club.club_id,
                },
            )

        for slot in club.players:
            self._upsert_player(club.game_id, slot.player)

        self._upsert_club(club)

        for slot in club.players:
            self._upsert_roster_entry(club, slot)

    def _upsert_player(self, game_id: str, player: Player):
        self._conn.execute(
            """
            INSERT INTO player (
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
                current_stamina,
                reputation
            )
            VALUES (
                :game_id,
                :player_id,
                :first_name,
                :second_name,
                :last_name,
                :age,
                :technique,
                :endurance,
                :exhaustion,
                :experience,
                :current_stamina,
                :reputation
            )
            ON CONFLICT(game_id, player_id) DO UPDATE SET
                first_name = excluded.first_name,
                second_name = excluded.second_name,
                last_name = excluded.last_name,
                age = excluded.age,
                technique = excluded.technique,
                endurance = excluded.endurance,
                exhaustion = excluded.exhaustion,
                experience = excluded.experience,
                current_stamina = excluded.current_stamina,
                reputation = excluded.reputation
            """,
            {
                "game_id": game_id,
                "player_id": player.player_id,
                "first_name": player.first_name,
                "second_name": player.second_name,
                "last_name": player.last_name,
                "age": player.age,
                "technique": player.technique,
                "endurance": player.endurance,
                "exhaustion": player.exhaustion,
                "experience": player.experience,
                "current_stamina": player.current_stamina,
                "reputation": player.reputation,
            },
        )

    def _upsert_club(self, club: Club):
        self._conn.execute(
            """
            INSERT INTO club (
                game_id,
                club_id,
                name,
                country,
                city,
                balance,
                coach_power,
                selected_player_id
            )
            VALUES (
                :game_id,
                :club_id,
                :name,
                :country,
                :city,
                :balance,
                :coach_power,
                :selected_player_id
            )
            ON CONFLICT(game_id, club_id) DO UPDATE SET
                name = excluded.name,
                country = excluded.country,
                city = excluded.city,
                balance = excluded.balance,
                coach_power = excluded.coach_power,
                selected_player_id = excluded.selected_player_id
            """,
            {
                "game_id": club.game_id,
                "club_id": club.club_id,
                "name": club.name,
                "country": None,
                "city": None,
                "balance": club.account.balance,
                "coach_power": club.coach_power,
                "selected_player_id": club._selected_player,
            },
        )

    def _upsert_roster_entry(self, club: Club, slot: ClubPlayerSlot):
        self._conn.execute(
            """
            INSERT INTO roster_entry (
                game_id,
                club_id,
                player_id,
                coach_level,
                contract_cost,
                has_next_contract
            )
            VALUES (
                :game_id,
                :club_id,
                :player_id,
                :coach_level,
                :contract_cost,
                :has_next_contract
            )
            ON CONFLICT(game_id, player_id) DO UPDATE SET
                club_id = excluded.club_id,
                coach_level = excluded.coach_level,
                contract_cost = excluded.contract_cost,
                has_next_contract = excluded.has_next_contract
            """,
            {
                "game_id": club.game_id,
                "club_id": club.club_id,
                "player_id": slot.player.player_id,
                "coach_level": slot.coach_level,
                "contract_cost": slot.contract_cost,
                "has_next_contract": int(slot.has_next_contract),
            },
        )
