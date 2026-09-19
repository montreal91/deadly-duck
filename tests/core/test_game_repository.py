"""
Created September 18, 2026

@author montreal91

Tests for game persistence.
"""

import sqlite3

from core.ports.outbound.game_repository import GameRepository


def test_does_game_exist_returns_true_for_saved_game_id():
    conn = _make_connection()
    conn.execute("INSERT INTO game (game_id) VALUES ('existing-game')")

    assert GameRepository(conn).does_game_exist("existing-game")


def test_does_game_exist_returns_false_for_unknown_game_id():
    conn = _make_connection()

    assert not GameRepository(conn).does_game_exist("missing-game")


def _make_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE game (
            game_id TEXT PRIMARY KEY NOT NULL,
            object BLOB,
            created_ts INTEGER,
            updated_ts INTEGER
        )
        """
    )
    return conn
