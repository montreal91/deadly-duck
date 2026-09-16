"""
Created September 16, 2026

@author montreal91
"""
import sqlite3

from core.player import Player
from core.ports.outbound.player_repository import PlayerRepository


def test_save_player_updates_existing_player():
    conn = _make_connection()
    repository = PlayerRepository(conn)
    player = repository.get_player("game", "player")

    assert player is not None

    player.age_up()
    player.add_experience(player.next_level_exp)
    player.add_reputation(7)
    player.add_exhaustion(3)

    repository.save_player(player)

    updated_player = repository.get_player("game", "player")

    assert updated_player is not None

    assert updated_player.age == 21
    assert updated_player.experience == player.experience
    assert updated_player.skill_points == player.skill_points
    assert updated_player.reputation == 7
    assert updated_player.exhaustion == 3


def test_get_all_active_players_returns_rostered_players_below_max_age():
    conn = _make_connection()
    repository = PlayerRepository(conn)

    players = repository.get_all_active_players("game", max_age=30)

    assert [
        player.player_id
        for player in players
    ] == ["player"]


def _make_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE game (
            game_id TEXT PRIMARY KEY NOT NULL
        );

        CREATE TABLE player (
            game_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            first_name TEXT NOT NULL,
            second_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            technique INTEGER NOT NULL,
            endurance INTEGER NOT NULL,
            exhaustion INTEGER NOT NULL,
            experience INTEGER NOT NULL,
            skill_points INTEGER NOT NULL,
            current_stamina INTEGER NOT NULL,
            reputation INTEGER NOT NULL,
            PRIMARY KEY (game_id, player_id)
        );

        CREATE TABLE club (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL,
            coach_power INTEGER NOT NULL,
            selected_player_id TEXT,
            PRIMARY KEY (game_id, club_id)
        );

        CREATE TABLE roster_entry (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            coach_level INTEGER NOT NULL,
            contract_cost INTEGER NOT NULL,
            has_next_contract INTEGER NOT NULL,
            PRIMARY KEY (game_id, player_id)
        );

        INSERT INTO game (game_id)
        VALUES ('game');

        INSERT INTO club (
            game_id,
            club_id,
            name,
            balance,
            coach_power
        )
        VALUES (
            'game',
            'club',
            'Club',
            0,
            1
        );
        """
    )
    _insert_player(conn, "game", "player", age=20)
    _insert_player(conn, "game", "retired-player", age=30)
    _insert_player(conn, "game", "free-agent", age=20)
    _insert_player(conn, "other-game", "other-game-player", age=20)
    conn.execute(
        """
        INSERT INTO roster_entry (
            game_id,
            club_id,
            player_id,
            coach_level,
            contract_cost,
            has_next_contract
        )
        VALUES
            ('game', 'club', 'player', 0, 0, 1),
            ('game', 'club', 'retired-player', 0, 0, 1)
        """
    )
    return conn


def _insert_player(conn, game_id, player_id, age):
    conn.execute(
        """
        INSERT OR IGNORE INTO game (game_id)
        VALUES (:game_id)
        """,
        {"game_id": game_id},
    )
    player = Player(
        first_name="First",
        second_name="Second",
        last_name="Last",
        age=age,
        technique=10,
        endurance=10,
    )
    player._player_id = player_id
    conn.execute(
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
            skill_points,
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
            :skill_points,
            :current_stamina,
            :reputation
        )
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
            "skill_points": player.skill_points,
            "current_stamina": player.current_stamina,
            "reputation": player.reputation,
        },
    )
