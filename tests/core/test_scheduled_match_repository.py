"""
Created September 11, 2026

@author montreal91
"""
import sqlite3

import pytest

from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.scheduled_match import ScheduledMatch


def test_save_matches_in_sqlite():
    conn = _make_connection()
    repository = ScheduledMatchRepository(conn)
    first_match = ScheduledMatch(
        home_pk="home",
        away_pk="away",
        competition_id="competition",
        schedule_day=2,
        match_id="first-match",
    )
    second_match = ScheduledMatch(
        home_pk="away",
        away_pk="home",
        competition_id="competition",
        schedule_day=2,
        match_id="second-match",
        playoff_series_id="series",
    )
    second_match.is_played = True

    repository.save_matches("game", [first_match, second_match])

    rows = conn.execute(
        """
        SELECT
            game_id,
            competition_id,
            match_id,
            schedule_day,
            position,
            home_club_id,
            away_club_id,
            playoff_series_id,
            is_played
        FROM scheduled_match
        ORDER BY position
        """
    ).fetchall()
    assert rows == [
        (
            "game",
            "competition",
            "first-match",
            2,
            0,
            "home",
            "away",
            None,
            0,
        ),
        (
            "game",
            "competition",
            "second-match",
            2,
            1,
            "away",
            "home",
            "series",
            1,
        ),
    ]


def test_save_matches_updates_existing_match():
    conn = _make_connection()
    repository = ScheduledMatchRepository(conn)
    match = ScheduledMatch(
        home_pk="home",
        away_pk="away",
        competition_id="competition",
        schedule_day=2,
        match_id="match",
    )
    repository.save_matches("game", [match])

    match.is_played = True
    repository.save_matches("game", [match])

    rows = conn.execute(
        """
        SELECT is_played
        FROM scheduled_match
        WHERE game_id = 'game'
          AND match_id = 'match'
        """
    ).fetchall()
    assert rows == [(1,)]


def test_save_matches_requires_sqlite_connection():
    repository = ScheduledMatchRepository()

    with pytest.raises(RuntimeError) as exc:
        repository.save_matches("game", [])

    assert str(exc.value) == "ScheduledMatchRepository has no SQLite connection."


def _make_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE game (
            game_id TEXT PRIMARY KEY NOT NULL
        );

        CREATE TABLE club (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            PRIMARY KEY (game_id, club_id),
            FOREIGN KEY (game_id) REFERENCES game(game_id)
        );

        CREATE TABLE competition (
            game_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            type TEXT NOT NULL,
            day INTEGER NOT NULL,
            season_index INTEGER NOT NULL,
            is_over INTEGER NOT NULL,
            PRIMARY KEY (game_id, competition_id),
            FOREIGN KEY (game_id) REFERENCES game(game_id)
        );

        CREATE TABLE scheduled_match (
            game_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            match_id TEXT NOT NULL,
            schedule_day INTEGER NOT NULL,
            position INTEGER NOT NULL,
            home_club_id TEXT NOT NULL,
            away_club_id TEXT NOT NULL,
            playoff_series_id TEXT,
            is_played INTEGER NOT NULL,
            PRIMARY KEY (game_id, match_id),
            UNIQUE (game_id, competition_id, schedule_day, position),
            FOREIGN KEY (game_id, competition_id)
                REFERENCES competition(game_id, competition_id),
            FOREIGN KEY (game_id, home_club_id)
                REFERENCES club(game_id, club_id),
            FOREIGN KEY (game_id, away_club_id)
                REFERENCES club(game_id, club_id)
        );

        INSERT INTO game (game_id)
        VALUES ('game');

        INSERT INTO club (game_id, club_id)
        VALUES
            ('game', 'home'),
            ('game', 'away');

        INSERT INTO competition (
            game_id,
            competition_id,
            type,
            day,
            season_index,
            is_over
        )
        VALUES (
            'game',
            'competition',
            'championship',
            0,
            0,
            0
        );
        """
    )
    return conn
