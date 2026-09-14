"""
Created September 14, 2026

@author montreal91
"""
import sqlite3

import pytest

from core.competition import CompetitionType
from core.ports.inbound.commands.next_day import NextDayCommand
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.regular_championship import RegularChampionship
from core.match_engine import MatchParams
from core.match import ExhaustionCalculator
from core.match import DdLinearProbabilityCalculator
from core.player import PlayerReputationCalculator
from core.regular_championship import ChampionshipParams


def test_save_competition_in_sqlite():
    conn = _make_connection()
    repository = CompetitionRepository(conn)
    competition = _competition("competition", day=2)

    repository.save(
        game_id="game",
        competition=competition,
        season_index=3,
    )

    rows = [
        tuple(row)
        for row in conn.execute(
        """
        SELECT
            game_id,
            competition_id,
            type,
            day,
            season_index,
            is_current
        FROM competition
        """
        ).fetchall()
    ]
    assert rows == [
        (
            "game",
            "competition",
            CompetitionType.CHAMPIONSHIP.value,
            2,
            3,
            1,
        ),
    ]


def test_save_competition_updates_existing_row_and_current_flag():
    conn = _make_connection()
    repository = CompetitionRepository(conn)
    first_competition = _competition("first-competition", day=2)
    second_competition = _competition("second-competition", day=0)

    repository.save("game", first_competition, season_index=0)
    first_competition._day = 3
    repository.save("game", first_competition, season_index=0)
    repository.save("game", second_competition, season_index=1)

    rows = [
        tuple(row)
        for row in conn.execute(
        """
        SELECT competition_id, day, season_index, is_current
        FROM competition
        ORDER BY competition_id
        """
        ).fetchall()
    ]
    assert rows == [
        ("first-competition", 3, 0, 0),
        ("second-competition", 0, 1, 1),
    ]


def test_save_competition_requires_sqlite_connection():
    repository = CompetitionRepository()

    with pytest.raises(RuntimeError) as exc:
        repository.save("game", _competition("competition"), season_index=0)

    assert str(exc.value) == "CompetitionRepository has no SQLite connection."


def test_next_day_handler_saves_current_competition():
    competition = _competition("competition", day=1)
    game = _Game(competition)
    competition_repository = _CompetitionRepository()
    handler = NextDayCommandHandler(
        game_repository=_GameRepository(game),
        club_repository=_ClubRepository(),
        competition_repository=competition_repository,
    )

    handler(NextDayCommand("game"))

    assert competition_repository.saved == [
        ("game", "competition", 0, True),
    ]


def test_next_day_handler_saves_replaced_competition_as_historical():
    previous_competition = _competition("previous-competition", day=4)
    next_competition = _competition("next-competition", day=0)
    game = _Game(previous_competition)

    def update():
        previous_competition._day = 5
        game.competition = next_competition
        game.season_index = 1
        return True, "Ok"

    game.update = update
    competition_repository = _CompetitionRepository()
    handler = NextDayCommandHandler(
        game_repository=_GameRepository(game),
        club_repository=_ClubRepository(),
        competition_repository=competition_repository,
    )

    handler(NextDayCommand("game"))

    assert competition_repository.saved == [
        ("game", "previous-competition", 0, False),
        ("game", "next-competition", 1, True),
    ]


def _competition(competition_id, day=0):
    competition = RegularChampionship(
        club_ids=["home", "away"],
        params=_championship_params(),
    )
    competition._competition_id = competition_id
    competition._day = day
    return competition


def _championship_params():
    match_params = MatchParams(
        games_to_win=1,
        sets_to_win=1,
        exhaustion_function=ExhaustionCalculator(1),
        probability_function=DdLinearProbabilityCalculator(0.003),
        reputation_function=PlayerReputationCalculator(1, 1),
    )
    return ChampionshipParams(
        match_params=match_params,
        recovery_day=2,
        rounds=2,
        match_importance=1,
    )


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
            is_current INTEGER NOT NULL,
            PRIMARY KEY (game_id, competition_id),
            FOREIGN KEY (game_id) REFERENCES game(game_id)
        );

        INSERT INTO game (game_id)
        VALUES ('game');
        """
    )
    return conn


class _Game:
    def __init__(self, competition):
        self.game_id = "game"
        self.competition = competition
        self.season_index = 0
        self.clubs = {}

    def update(self):
        return True, "Ok"


class _GameRepository:
    def __init__(self, game):
        self._game = game
        self.saved_game = None

    def get_game(self, _game_id):
        return self._game

    def save_game(self, game):
        self.saved_game = game


class _ClubRepository:
    def save_clubs(self, _clubs):
        pass


class _CompetitionRepository:
    def __init__(self):
        self.saved = []

    def save(
            self,
            game_id,
            competition,
            season_index,
            is_current=True,
    ):
        self.saved.append((
            game_id,
            competition.competition_id,
            season_index,
            is_current,
        ))
