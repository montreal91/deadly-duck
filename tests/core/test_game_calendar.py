"""
Created Aug 22, 2026

@author montreal91
"""
import sqlite3
from datetime import date
from unittest.mock import Mock

import pytest

from core.competition import CompetitionType
from core.game import Game
from core.playoffs import Playoff
from core.ports.outbound.competition_repository import CompetitionRepository
from tests.core.fixtures.game import make_game
from tests.core.fixtures.game import make_persisted_game


def test_game_starts_on_first_season_calendar_date(tmp_path):
    game, _, _ = make_persisted_game("calendar-test", tmp_path / "game.sqlite")

    assert game.current_date == date(2082, 2, 21)
    assert game.get_context(_first_club_id(game))["day"] == "2082-Feb-21"


def test_successful_game_update_advances_calendar_date(tmp_path):
    game, clubs, _ = make_persisted_game("calendar-test", tmp_path / "game.sqlite")

    success, _ = game.update(clubs)

    assert success
    assert game.current_date == date(2082, 2, 22)
    assert game.get_context(_first_club_id(game))["day"] == "2082-Feb-22"


def test_next_season_starts_on_next_year_february_21(tmp_path):
    game, clubs, _ = make_persisted_game("calendar-test", tmp_path / "game.sqlite")
    game._history[-1][CompetitionType.CHAMPIONSHIP] = game.cmp.standings

    game._next_season(clubs)
    game._advance_current_date()

    assert game.current_date == date(2083, 2, 21)
    assert game.get_context(_first_club_id(game))["day"] == "2083-Feb-21"


def test_next_season_ages_and_rests_roster_players(tmp_path):
    game, clubs, _ = make_persisted_game(
        "season-end-test",
        tmp_path / "season-end.sqlite",
    )
    player = next(iter(clubs.values())).players[0].player
    initial_age = player.age
    player.add_exhaustion(10)

    game._next_season(clubs)

    assert player.age == initial_age + 1
    assert player.exhaustion == 0


def test_regular_season_end_starts_playoffs(tmp_path):
    game, clubs, _ = make_persisted_game(
        "calendar-test",
        tmp_path / "game.sqlite",
    )
    regular_season_length = len(game.cmp._schedule)

    for _ in range(regular_season_length):
        success, reason = game.update(clubs)
        assert success, reason

    assert isinstance(game.cmp, Playoff)


@pytest.mark.skip
def test_game_starts_playoff_with_top_regular_season_clubs():
    # TODO: fix this test
    conn = _make_connection()
    CompetitionRepository.tmp_initialize(conn)
    game = make_game("calendar-test")

    game._start_playoff()

    assert game.cmp.contains_club("0")
    assert game.cmp.contains_club("7")
    assert not game.cmp.contains_club("8")
    assert not game.cmp.contains_club("9")


@pytest.mark.skip
def test_proceed_skips_competition_when_manager_club_is_not_participating(monkeypatch):
    competition_repository = Mock()
    competition = Mock()
    competition.day = 1
    competition_repository.get_ongoing_competitions.return_value = [competition]
    monkeypatch.setattr(CompetitionRepository, "_INSTANCE", competition_repository)
    game = Game.__new__(Game)
    game._game_id = "calendar-test"
    game._manager_club_id = "manager"
    updates = []

    def update():
        updates.append(1)
        return False, "Stopped"

    game.update = update

    game.proceed_to_next_competition()

    assert len(updates) == 1


def _first_club_id(game):
    return next(iter(game.clubs))


def _make_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE game (
            game_id TEXT PRIMARY KEY NOT NULL,
            object BLOB,
            created_ts INTEGER,
            updated_ts INTEGER
        );

        CREATE TABLE competition (
            game_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            type TEXT NOT NULL,
            day INTEGER NOT NULL,
            season_index INTEGER NOT NULL,
            is_over INTEGER NOT NULL,
            object BLOB,
            PRIMARY KEY (game_id, competition_id)
        );

        CREATE TABLE club (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            PRIMARY KEY (game_id, club_id)
        );

        CREATE TABLE playoff_series (
            game_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            series_id TEXT NOT NULL,
            round_number INTEGER NOT NULL,
            position INTEGER NOT NULL,
            top_club_id TEXT,
            bottom_club_id TEXT,
            PRIMARY KEY (game_id, series_id),
            FOREIGN KEY (game_id, top_club_id)
                REFERENCES club(game_id, club_id),
            FOREIGN KEY (game_id, bottom_club_id)
                REFERENCES club(game_id, club_id)
        );

        INSERT INTO game (game_id)
        VALUES ('calendar-test');
        """
    )
    return conn


def _insert_clubs(conn, game):
    with conn:
        for club_id in game.clubs:
            conn.execute(
                """
                INSERT INTO club (game_id, club_id)
                VALUES (:game_id, :club_id)
                """,
                {
                    "game_id": game.game_id,
                    "club_id": club_id,
                },
            )
