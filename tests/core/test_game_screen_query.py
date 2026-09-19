"""
Created Aug 24, 2026

@author montreal91
"""
from types import SimpleNamespace
from unittest.mock import Mock

from core.competition import CompetitionType
from core.playoffs import Playoff
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.queries.game_screen_query import GameScreenGuiQueryHandler
from core.queries.game_screen_query import PlayoffStandings
from core.regular_championship import RegularChampionship
from core.regular_championship import RegularChampionshipStandingsRow
from core.scheduled_match import ScheduledMatch
from tests.core.fixtures.game import make_persisted_game
from tests.core.fixtures.game import make_game_params


def test_game_screen_query_converts_remaining_matches_to_upcoming_days():
    first_match = ScheduledMatch("manager", "opponent")
    second_match = ScheduledMatch("opponent", "manager")
    game = _game(
        current_matches=[first_match],
        remaining_matches=[first_match, None, second_match],
    )
    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider({
            "manager": _club("Manager Club"),
            "opponent": _club("Opponent Club"),
        }),
        match_result_repository=_match_result_repository(),
        competition_repository=_competition_repository(game),
    )

    result = handler("game", "manager")

    assert result.upcoming_days[0].day == "2082-Feb-21"
    assert result.upcoming_days[0].match.opponent_club_name == "Opponent Club"
    assert result.upcoming_days[0].match.home_away == "Home"
    assert result.upcoming_days[1].day == "2082-Feb-22"
    assert result.upcoming_days[1].match is None
    assert result.upcoming_days[2].day == "2082-Feb-23"
    assert result.upcoming_days[2].match.opponent_club_name == "Opponent Club"
    assert result.upcoming_days[2].match.home_away == "Away"


def test_game_screen_query_uses_empty_scores_for_future_playoff_series():
    game = _game(
        current_matches=[],
        remaining_matches=[],
        competition_type=CompetitionType.PLAY_OFFS,
        standings=[
            {
                "clubs": ("manager", "opponent"),
                "score": (0, 0),
                "seeds": (1, 4),
            },
            {
                "clubs": ("other-1", "other-2"),
                "score": (0, 0),
                "seeds": (2, 3),
            },
        ],
    )
    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider({
            "manager": _club("Manager Club"),
            "opponent": _club("Opponent Club"),
            "other-1": _club("Other Club 1"),
            "other-2": _club("Other Club 2"),
        }),
        match_result_repository=_match_result_repository(),
        competition_repository=_competition_repository(game),
    )

    result = handler("game", "manager")

    assert isinstance(result.standings, PlayoffStandings)
    assert result.standings.rows[0].top_seed == 1
    assert result.standings.rows[0].bottom_seed == 4
    assert result.standings.rows[1].top_seed == 2
    assert result.standings.rows[1].bottom_seed == 3
    assert result.standings.rows[2].top_seed == ""
    assert result.standings.rows[2].bottom_seed == ""
    assert result.standings.rows[2].top_score == ""
    assert result.standings.rows[2].bottom_score == ""


def test_game_screen_query_supports_twelve_club_preliminary_round():
    game = _game(
        current_matches=[],
        remaining_matches=[],
        competition_type=CompetitionType.PLAY_OFFS,
        standings=[
            {
                "clubs": ("seed-1", None),
                "score": ("", ""),
                "seeds": (1, ""),
                "round_number": 1,
            },
            {
                "clubs": ("seed-5", "seed-12"),
                "score": (0, 0),
                "seeds": (5, 12),
                "round_number": 1,
            },
            {
                "clubs": ("seed-3", None),
                "score": ("", ""),
                "seeds": (3, ""),
                "round_number": 1,
            },
            {
                "clubs": ("seed-6", "seed-11"),
                "score": (0, 0),
                "seeds": (6, 11),
                "round_number": 1,
            },
            {
                "clubs": ("seed-2", None),
                "score": ("", ""),
                "seeds": (2, ""),
                "round_number": 1,
            },
            {
                "clubs": ("seed-7", "seed-10"),
                "score": (0, 0),
                "seeds": (7, 10),
                "round_number": 1,
            },
            {
                "clubs": ("seed-4", None),
                "score": ("", ""),
                "seeds": (4, ""),
                "round_number": 1,
            },
            {
                "clubs": ("seed-8", "seed-9"),
                "score": (0, 0),
                "seeds": (8, 9),
                "round_number": 1,
            },
        ],
    )
    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider({
            f"seed-{seed}": _club(f"Seed {seed}")
            for seed in range(1, 13)
        }),
        match_result_repository=_match_result_repository(),
        competition_repository=_competition_repository(game),
    )

    result = handler("game", "seed-5")

    assert [row.round_number for row in result.standings.rows].count(1) == 8
    assert [row.round_number for row in result.standings.rows].count(2) == 4
    assert [row.round_number for row in result.standings.rows].count(3) == 2
    assert [row.round_number for row in result.standings.rows].count(4) == 1
    assert result.standings.rows[0].bottom_club_name == "BYE"
    assert result.standings.rows[0].bottom_seed == ""


def test_game_screen_query_after_playoff_end_does_not_crash(tmp_path):
    game, clubs, _ = make_persisted_game(
        "calendar-test",
        tmp_path / "game.sqlite",
    )
    cmp = game.cmp

    if cmp is None:
        assert False, "This should not happen."

    regular_season_length = len(cmp._schedule or [])

    for _ in range(regular_season_length + 9):
        success, reason = game.update(clubs)
        assert success, reason

    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider(game.clubs),
        match_result_repository=MatchResultRepository.tmp_get_instance(),
        competition_repository=CompetitionRepository.tmp_get_instance(),
    )

    handler("calendar-test", _first_club_id(game))


def test_game_screen_query_shows_bracket_when_playoffs_start(tmp_path):
    game, clubs, _ = make_persisted_game(
        "playoff-bracket-test",
        tmp_path / "game.sqlite",
    )

    regular_season_length = len(game.cmp._schedule)
    for _ in range(regular_season_length):
        success, reason = game.update(clubs)
        assert success, reason

    assert isinstance(game.cmp, Playoff)

    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider(clubs),
        match_result_repository=MatchResultRepository.tmp_get_instance(),
        competition_repository=CompetitionRepository.tmp_get_instance(),
    )

    result = handler("playoff-bracket-test", _first_club_id(game))

    assert isinstance(result.standings, PlayoffStandings)
    assert result.standings.rows


def test_game_screen_query_returns_only_manager_master_league_data():
    game = _game(current_matches=[], remaining_matches=[])
    master_competition = RegularChampionship(
        ["master-manager", "master-opponent"],
        make_game_params().championship_params,
    )
    apprentice_competition = RegularChampionship(
        ["farm-manager", "farm-opponent"],
        make_game_params().championship_params,
    )
    master_competition._competition_id = "master-competition"
    apprentice_competition._competition_id = "apprentice-competition"
    competition_repository = Mock()
    competition_repository.get_ongoing_competitions.return_value = [
        apprentice_competition,
        master_competition,
    ]
    match_result_repository = Mock()
    match_result_repository.get_regular_championship_standings.return_value = [
        RegularChampionshipStandingsRow("master-manager", 1, 2, 12),
        RegularChampionshipStandingsRow("master-opponent", 1, 0, 8),
    ]
    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider({
            "master-manager": _club("Master Manager"),
            "master-opponent": _club("Master Opponent"),
            "farm-manager": _club("Farm Manager"),
            "farm-opponent": _club("Farm Opponent"),
        }),
        match_result_repository=match_result_repository,
        competition_repository=competition_repository,
    )

    result = handler("game", "master-manager")

    assert [row.club_id for row in result.standings.rows] == [
        "master-manager",
        "master-opponent",
    ]
    match_result_repository.get_regular_championship_standings.assert_called_once_with(
        "game",
        "master-competition",
    )


def _create_schedule_result_tables(conn):
    conn.executescript(
        """
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
            PRIMARY KEY (game_id, match_id)
        );
        """
    )


def _game_repository(game):
    repository = Mock()
    repository.get_game.return_value = game
    return repository


def _club_provider(clubs):
    provider = Mock()
    provider.get_clubs_for_game.return_value = clubs
    return provider


def _match_result_repository(standings=None):
    repository = Mock()
    repository.get_regular_championship_standings.return_value = standings or []
    return repository


def _competition_repository(game):
    repository = Mock()
    repository.get_ongoing_competitions.return_value = [game.cmp]
    return repository


def _game(
        current_matches,
        remaining_matches,
        competition_type=CompetitionType.CHAMPIONSHIP,
        standings=None,
):
    game = Mock()
    game.cmp = SimpleNamespace(
        competition_id="competition",
        current_matches=current_matches,
    )
    game.get_context.return_value = {
        "day": "2082-Feb-21",
        "history": [{}],
        "balance": 0,
        "club_name": "Manager Club",
        "competition": "Regular Season",
        "competition_type": competition_type,
        "has_matches": True,
        "remaining_matches": remaining_matches,
        "standings": standings or [],
    }
    return game


def _club(name):
    club = Mock()
    club.name = name
    club.players = []
    return club


def _first_club_id(game):
    return next(iter(game.clubs))
