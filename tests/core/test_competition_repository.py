"""
Created September 14, 2026

@author montreal91
"""
import sqlite3

import pytest

from core.competition import AbstractCompetition
from core.competition import CompetitionType
from core.match import DdLinearProbabilityCalculator
from core.match import ExhaustionCalculator
from core.match_engine import MatchParams
from core.player import PlayerReputationCalculator
from core.ports.inbound.commands.next_day import NextDayCommand
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.regular_championship import ChampionshipParams
from core.regular_championship import RegularChampionship
from tests.core.fixtures.game import make_game


def test_save_competition_in_sqlite():
    conn = _make_connection()
    repository = CompetitionRepository(conn)
    competition = _competition("competition", day=2)

    repository.save_competition(
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
            is_over
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
            0,
        ),
    ]


def test_save_competition_updates_existing_row_and_over_flag():
    conn = _make_connection()
    repository = CompetitionRepository(conn)
    first_competition = _competition("first-competition", day=2)
    second_competition = _competition("second-competition", day=0)

    repository.save_competition("game", first_competition, season_index=0)
    first_competition._day = 3
    repository.save_competition("game", first_competition, season_index=0)
    repository.save_competition("game", first_competition, season_index=0)
    repository.save_competition("game", second_competition, season_index=1)

    rows = [
        tuple(row)
        for row in conn.execute(
        """
        SELECT competition_id, day, season_index, is_over
        FROM competition
        ORDER BY competition_id
        """
        ).fetchall()
    ]
    assert rows == [
        ("first-competition", 3, 0, 0),
        ("second-competition", 0, 1, 0),
    ]


def test_next_day_handler_saves_current_competition():
    conn = _make_connection()
    CompetitionRepository.temporal_initialize(conn)
    competition_repository = CompetitionRepository.temporal_get_instance()

    game_repository = GameRepository(conn)
    game = make_game("game")
    game_repository.save_game(game)

    handler = NextDayCommandHandler(
        game_repository=game_repository,
        club_repository=_ClubRepository(),
        competition_repository=competition_repository,
    )

    handler(NextDayCommand("game"))

    updated_competition: AbstractCompetition = competition_repository.get_ongoing_competitions("game")[0]
    actual = (updated_competition.title, updated_competition.day, updated_competition.is_over)

    assert actual == ("Regular Season", 1, False)

    handler(NextDayCommand("game"))
    updated_competition: AbstractCompetition = competition_repository.get_ongoing_competitions("game")[0]
    actual = (updated_competition.title, updated_competition.day, updated_competition.is_over)
    assert actual == ("Regular Season", 2, False)

@pytest.mark.skip
def test_next_day_handler_saves_replaced_competition_as_historical():
    # TODO: Fix this test if necessary
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
        ("game", "previous-competition", 0, True),
        ("game", "next-competition", 1, False),
    ]


def _competition(competition_id: str, day: int = 0):
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


def _make_connection() -> sqlite3.Connection:
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
            is_over=False,
    ):
        self.saved.append((
            game_id,
            competition.competition_id,
            season_index,
            is_over,
        ))
