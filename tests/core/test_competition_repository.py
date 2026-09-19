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
from core.match_result import MatchResult
from core.player import PlayerReputationCalculator
from core.ports.inbound.commands.create_new_game import init_clubs_for_game
from core.ports.inbound.commands.next_day import NextDayCommand
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.playoffs import Playoff
from core.playoffs import PlayoffParams
from core.playoffs import PlayoffSeed
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.regular_championship import ChampionshipParams
from core.regular_championship import RegularChampionship
from core.set_result import DdSetStatuses
from core.set_result import SetResult
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


def test_get_season_competitions_returns_competitions_for_requested_season():
    conn = _make_connection()
    repository = CompetitionRepository(conn)
    previous_season_competition = _competition("previous-season", day=5)
    first_competition = _competition("first-competition", day=2)
    second_competition = _competition("second-competition", day=0)
    second_competition._is_over = True

    repository.save_competition("game", previous_season_competition, season_index=0)
    repository.save_competition("game", first_competition, season_index=1)
    repository.save_competition("game", second_competition, season_index=1)

    competitions = repository.get_season_competitions(
        game_id="game",
        season_index=1,
    )

    assert [
        (competition.competition_id, competition.day, competition.is_over)
        for competition in competitions
    ] == [
        ("second-competition", 0, True),
        ("first-competition", 2, False),
    ]


def test_save_playoff_competition_inserts_playoff_series():
    conn = _make_connection()
    _insert_playoff_clubs(conn)
    repository = CompetitionRepository(conn)
    playoff = _playoff("playoff")

    repository.save_competition("game", playoff, season_index=0)

    rows = [
        tuple(row)
        for row in conn.execute(
        """
        SELECT competition_id, series_id, round_number
        FROM playoff_series
        ORDER BY round_number, series_id
        """
        ).fetchall()
    ]

    assert rows == [
        (
            "playoff",
            series.series_id,
            series.round_number,
        )
        for series in sorted(
            playoff._series,
            key=lambda series: (series.round_number, series.series_id),
        )
    ]


def test_get_ongoing_playoff_competitions_loads_series_from_table():
    conn = _make_connection()
    _insert_playoff_clubs(conn)
    repository = CompetitionRepository(conn)
    playoff = _playoff("playoff")
    first_series = playoff._series[0]
    repository.save_competition("game", playoff, season_index=0)
    conn.execute(
        """
        UPDATE playoff_series
        SET top_club_id = '7',
            bottom_club_id = '6'
        WHERE game_id = 'game'
          AND series_id = :series_id
        """,
        {"series_id": first_series.series_id},
    )

    loaded_playoff = repository.get_ongoing_competitions("game")[0]
    loaded_series = loaded_playoff._series_by_id[first_series.series_id]

    assert loaded_series.pair == ("7", "6")


def test_get_ongoing_playoff_competitions_preserves_series_results():
    conn = _make_connection()
    _insert_playoff_clubs(conn)
    repository = CompetitionRepository(conn)
    playoff = _playoff("playoff")
    playoff.apply_results([
        _match_result(match)
        for match in playoff.current_matches
    ])
    expected_scores = [
        series.score
        for series in playoff._past_series
    ]
    repository.save_competition("game", playoff, season_index=0)

    loaded_playoff = repository.get_ongoing_competitions("game")[0]

    assert [
        series.score
        for series in loaded_playoff._past_series
    ] == expected_scores


def test_next_day_handler_saves_current_competition():
    conn = _make_connection()
    CompetitionRepository.tmp_initialize(conn)
    ScheduledMatchRepository.tmp_init(conn)
    MatchResultRepository.tmp_init(conn)
    TemporalClubProvider.initialize(conn)

    game_repository = GameRepository(conn)
    TemporalClubProvider.get_instance().save_clubs(init_clubs_for_game("game").values())

    game = make_game(game_id="game", conn=conn)
    game_repository.save_game(game)

    competitions = CompetitionRepository.tmp_get_instance().get_ongoing_competitions("game")

    assert competitions, "Competitions should exist"

    cmp = competitions[0]
    assert cmp.day == 0

    competition_repository = CompetitionRepository.tmp_get_instance()
    handler = NextDayCommandHandler(
        game_repository=game_repository,
        club_repository=TemporalClubProvider.get_instance(),
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


def _playoff(competition_id: str):
    playoff = Playoff(
        params=_playoff_params(),
        seeds=[
            PlayoffSeed(club_id=str(i), seed=i + 1)
            for i in range(8)
        ],
    )
    playoff._competition_id = competition_id
    return playoff


def _match_result(match):
    result = MatchResult()
    result.match_id = match.match_id
    result.home_pk = match.home_pk
    result.away_pk = match.away_pk
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


def _playoff_params():
    match_params = MatchParams(
        games_to_win=1,
        sets_to_win=1,
        exhaustion_function=ExhaustionCalculator(1),
        probability_function=DdLinearProbabilityCalculator(0.003),
        reputation_function=PlayerReputationCalculator(1, 1),
    )
    return PlayoffParams(
        match_params=match_params,
        series_matches_pattern=(True,),
        length=8,
        gap_days=0,
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

        CREATE TABLE club (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            name TEXT,
            balance INTEGER,
            coach_power INTEGER,
            league_id TEXT,
            selected_player_id TEXT,
            PRIMARY KEY (game_id, club_id)
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

        CREATE TABLE roster_entry (
            game_id TEXT NOT NULL,
            club_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            coach_level INTEGER NOT NULL,
            contract_cost INTEGER,
            has_next_contract INTEGER NOT NULL,
            PRIMARY KEY (game_id, player_id)
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
            PRIMARY KEY (game_id, match_id)
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
            FOREIGN KEY (game_id, match_id)
                REFERENCES scheduled_match(game_id, match_id)
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
        """
    )
    return conn


def _insert_playoff_clubs(conn):
    with conn:
        conn.executemany(
            "INSERT INTO club (game_id, club_id) VALUES ('game', ?)",
            [(str(club_id),) for club_id in range(8)],
        )


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
