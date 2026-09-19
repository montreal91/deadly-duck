"""
Created September 15, 2026

@author montreal91
"""
import sqlite3

import pytest

from core.match_result import MatchResult
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.regular_championship import RegularChampionshipStandingsRow
from core.set_result import DdSetStatuses
from core.set_result import SetResult


def test_save_match_results_in_sqlite():
    conn = _make_connection()
    repository = MatchResultRepository(conn)
    result = _match_result("match")

    repository.save_match_results("game", [result])

    rows = [
        tuple(row)
        for row in conn.execute(
            """
            SELECT
                game_id,
                competition_id,
                match_id,
                home_club_id,
                away_club_id,
                home_sets,
                away_sets,
                home_games,
                away_games,
                full_score,
                attendance,
                income
            FROM match_result
            """
        ).fetchall()
    ]

    assert rows == [
        (
            "game",
            "competition",
            "match",
            "home",
            "away",
            2,
            0,
            12,
            8,
            "6:4 6:4",
            100,
            200,
        ),
    ]


def test_get_latest_results_returns_results_from_latest_competition_day():
    conn = _make_connection()
    repository = MatchResultRepository(conn)
    older_result = _match_result("match")
    latest_result = _match_result("latest-match")
    other_competition_result = _match_result(
        "other-competition-match",
        home_pk="other-home",
        away_pk="other-away",
    )
    repository.save_match_results("game", [
        older_result,
        latest_result,
        other_competition_result,
    ])

    results = repository.get_latest_results("game", "competition")

    assert len(results) == 1
    assert results[0].match_id == "latest-match"
    assert results[0].home_pk == "home"
    assert results[0].away_pk == "away"
    assert results[0].home_player_snapshot["first_name"] == "Home"
    assert results[0].away_player_snapshot["first_name"] == "Away"
    assert results[0].home_sets == 2
    assert results[0].away_sets == 0
    assert results[0].home_games == 12
    assert results[0].away_games == 8
    assert results[0].full_score == "6:4 6:4"
    assert results[0].attendance == 100
    assert results[0].income == 200


def test_get_regular_championship_standings_from_persisted_results():
    conn = _make_connection()
    repository = MatchResultRepository(conn)
    repository.save_match_results("game", [
        _match_result("match"),
        _match_result("latest-match"),
    ])

    standings = repository.get_regular_championship_standings(
        "game",
        "competition",
    )

    assert standings == [
        RegularChampionshipStandingsRow(
            club_id="home",
            matches_played=2,
            sets_won=4,
            games_won=24,
        ),
        RegularChampionshipStandingsRow(
            club_id="away",
            matches_played=2,
            sets_won=0,
            games_won=16,
        ),
        RegularChampionshipStandingsRow(
            club_id="other-home",
            matches_played=0,
            sets_won=0,
            games_won=0,
        ),
        RegularChampionshipStandingsRow(
            club_id="other-away",
            matches_played=0,
            sets_won=0,
            games_won=0,
        ),
    ]


def test_save_match_results_requires_sqlite_connection():
    repository = MatchResultRepository()

    with pytest.raises(RuntimeError) as exc:
        repository.save_match_results("game", [])

    assert str(exc.value) == "MatchResultRepository has no SQLite connection."


def test_get_latest_results_requires_sqlite_connection():
    repository = MatchResultRepository()

    with pytest.raises(RuntimeError) as exc:
        repository.get_latest_results("game", "competition")

    assert str(exc.value) == "MatchResultRepository has no SQLite connection."


def test_get_regular_championship_standings_requires_sqlite_connection():
    repository = MatchResultRepository()

    with pytest.raises(RuntimeError) as exc:
        repository.get_regular_championship_standings("game", "competition")

    assert str(exc.value) == "MatchResultRepository has no SQLite connection."


def _match_result(match_id, home_pk="home", away_pk="away"):
    result = MatchResult()
    result.match_id = match_id
    result.home_pk = home_pk
    result.away_pk = away_pk
    result.home_player_snapshot = _player("Home")
    result.away_player_snapshot = _player("Away")
    result.attendance = 100
    result.income = 200
    result.AddSetResult(SetResult(
        home_games=6,
        away_games=4,
        set_status=DdSetStatuses.REGULAR,
    ))
    result.AddSetResult(SetResult(
        home_games=6,
        away_games=4,
        set_status=DdSetStatuses.REGULAR,
    ))
    return result


def _player(first_name):
    return {
        "first_name": first_name,
        "second_name": "Second",
        "last_name": "Player",
    }


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
            home_club_id TEXT NOT NULL,
            away_club_id TEXT NOT NULL,
            playoff_series_id TEXT,
            is_played INTEGER NOT NULL,
            PRIMARY KEY (game_id, match_id),
            FOREIGN KEY (game_id, competition_id)
                REFERENCES competition(game_id, competition_id),
            FOREIGN KEY (game_id, home_club_id)
                REFERENCES club(game_id, club_id),
            FOREIGN KEY (game_id, away_club_id)
                REFERENCES club(game_id, club_id)
        );

        CREATE TABLE match_result (
            game_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            match_id TEXT NOT NULL,
            home_club_id TEXT NOT NULL,
            away_club_id TEXT NOT NULL,
            home_player_id TEXT,
            away_player_id TEXT,
            home_player_snapshot TEXT,
            away_player_snapshot TEXT,
            home_sets INTEGER NOT NULL,
            away_sets INTEGER NOT NULL,
            home_games INTEGER NOT NULL,
            away_games INTEGER NOT NULL,
            full_score TEXT NOT NULL,
            attendance INTEGER NOT NULL,
            income INTEGER NOT NULL,
            PRIMARY KEY (game_id, match_id),
            FOREIGN KEY (game_id, competition_id)
                REFERENCES competition(game_id, competition_id),
            FOREIGN KEY (game_id, match_id)
                REFERENCES scheduled_match(game_id, match_id),
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
            ('game', 'away'),
            ('game', 'other-home'),
            ('game', 'other-away');

        INSERT INTO competition (
            game_id,
            competition_id,
            type,
            day,
            season_index,
            is_over
        )
        VALUES
            ('game', 'competition', 'championship', 0, 0, 0),
            ('game', 'other-competition', 'championship', 0, 0, 0);

        INSERT INTO scheduled_match (
            game_id,
            competition_id,
            match_id,
            schedule_day,
            home_club_id,
            away_club_id,
            is_played
        )
        VALUES
            ('game', 'competition', 'match', 1, 'home', 'away', 1),
            ('game', 'competition', 'latest-match', 2, 'home', 'away', 1),
            ('game', 'competition', 'future-match', 3, 'other-home', 'other-away', 0),
            (
                'game',
                'other-competition',
                'other-competition-match',
                4,
                'other-home',
                'other-away',
                1
            );
        """
    )
    return conn
