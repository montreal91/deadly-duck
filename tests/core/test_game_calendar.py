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
from core.ports.inbound.commands.next_day import NextDayCommand
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
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


def test_regular_season_practice_day_persists_player_experience(tmp_path):
    game, clubs, conn = make_persisted_game(
        "practice-test",
        tmp_path / "practice.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    player = clubs[club_id].players[0].player
    conn.execute(
        """
        UPDATE roster_entry
        SET coach_level = 1
        WHERE game_id = ? AND player_id = ?
        """,
        ("practice-test", player.player_id),
    )
    conn.commit()
    initial_experience, current_stamina = conn.execute(
        """
        SELECT experience, current_stamina
        FROM player
        WHERE game_id = ? AND player_id = ?
        """,
        ("practice-test", player.player_id),
    ).fetchone()
    assert game.cmp.current_matches == []
    handler = NextDayCommandHandler(
        game_repository=game_repository,
        club_repository=TemporalClubProvider.get_instance(),
        competition_repository=CompetitionRepository.tmp_get_instance(),
    )

    result = handler(NextDayCommand("practice-test"))

    persisted_experience = conn.execute(
        """
        SELECT experience
        FROM player
        WHERE game_id = ? AND player_id = ?
        """,
        ("practice-test", player.player_id),
    ).fetchone()[0]
    assert result.success
    assert persisted_experience == initial_experience + current_stamina


def test_regular_season_match_day_persists_club_income(tmp_path):
    game, clubs, conn = make_persisted_game(
        "income-test",
        tmp_path / "income.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    handler = NextDayCommandHandler(
        game_repository=game_repository,
        club_repository=TemporalClubProvider.get_instance(),
        competition_repository=CompetitionRepository.tmp_get_instance(),
    )
    practice_day_result = handler(NextDayCommand("income-test"))
    balance_before_match = conn.execute(
        """
        SELECT balance
        FROM club
        WHERE game_id = ? AND club_id = ?
        """,
        ("income-test", club_id),
    ).fetchone()[0]

    match_day_result = handler(NextDayCommand("income-test"))

    persisted_balance = conn.execute(
        """
        SELECT balance
        FROM club
        WHERE game_id = ? AND club_id = ?
        """,
        ("income-test", club_id),
    ).fetchone()[0]
    assert practice_day_result.success
    assert match_day_result.success
    assert persisted_balance == balance_before_match + 250_000


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


def test_next_season_consumes_players_next_contract(tmp_path):
    game, clubs, _ = make_persisted_game(
        "contract-test",
        tmp_path / "contract.sqlite",
    )
    club = next(iter(clubs.values()))
    player_slot = club.players[0]
    player_slot.has_next_contract = True

    game._next_season(clubs)

    renewed_slot = club.get_player_slot(player_slot.player.player_id)
    assert renewed_slot is not None
    assert not renewed_slot.has_next_contract


def test_next_season_releases_player_without_next_contract(tmp_path):
    game, clubs, _ = make_persisted_game(
        "expired-contract-test",
        tmp_path / "expired-contract.sqlite",
    )
    club = next(iter(clubs.values()))
    player_slot = club.players[0]
    player_slot.has_next_contract = False

    game._next_season(clubs)

    assert not club.has_player(player_slot.player.player_id)


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


def test_regular_seasons_start_separate_playoffs_for_each_league(tmp_path):
    game, clubs, _ = make_persisted_game(
        "league-playoffs-test",
        tmp_path / "game.sqlite",
    )
    competition_repository = CompetitionRepository.tmp_get_instance()
    regular_seasons = competition_repository.get_ongoing_competitions(game.game_id)
    regular_season_length = max(
        len(competition._schedule)
        for competition in regular_seasons
    )

    for _ in range(regular_season_length):
        success, reason = game.update(clubs)
        assert success, reason

    playoffs = [
        competition
        for competition in competition_repository.get_ongoing_competitions(
            game.game_id,
        )
        if isinstance(competition, Playoff)
    ]
    master_club_ids = {
        club_id
        for club_id, club in clubs.items()
        if club.league_id == "master_league"
    }
    apprentice_club_ids = {
        club_id
        for club_id, club in clubs.items()
        if club.league_id == "apprentice_league"
    }

    assert len(playoffs) == 2
    assert any(
        set(playoff._club_ids) <= master_club_ids
        for playoff in playoffs
    )
    assert any(
        set(playoff._club_ids) <= apprentice_club_ids
        for playoff in playoffs
    )
    assert all(
        not (
            set(playoff._club_ids) & master_club_ids
            and set(playoff._club_ids) & apprentice_club_ids
        )
        for playoff in playoffs
    )


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
