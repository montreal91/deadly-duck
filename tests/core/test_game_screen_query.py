"""
Created Aug 24, 2026

@author montreal91
"""
from types import SimpleNamespace
from unittest.mock import Mock

from core.competition import CompetitionType
from core.ports.outbound.competition_repository import CompetitionRepository
from core.queries.game_screen_query import GameScreenGuiQueryHandler
from core.queries.game_screen_query import PlayoffStandings
from core.scheduled_match import ScheduledMatch
from tests.core.fixtures.game import make_game
from tests.core.test_game_calendar import _insert_clubs
from tests.core.test_game_calendar import _make_connection


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
    )

    result = handler("game", "seed-5")

    assert [row.round_number for row in result.standings.rows].count(1) == 8
    assert [row.round_number for row in result.standings.rows].count(2) == 4
    assert [row.round_number for row in result.standings.rows].count(3) == 2
    assert [row.round_number for row in result.standings.rows].count(4) == 1
    assert result.standings.rows[0].bottom_club_name == "BYE"
    assert result.standings.rows[0].bottom_seed == ""


def test_game_screen_query_after_playoff_end_does_not_crash():
    conn = _make_connection()
    CompetitionRepository.temporal_initialize(conn)
    game = make_game("calendar-test")
    _insert_clubs(conn, game)
    cmp = game.cmp

    if cmp is None:
        assert False, "This should not happen."

    regular_season_length = len(cmp._schedule or [])

    for _ in range(regular_season_length + 9):
        success, reason = game.update()
        assert success, reason

    handler = GameScreenGuiQueryHandler(
        game_repository=_game_repository(game),
        club_provider=_club_provider(game.clubs),
    )

    handler("calendar-test", _first_club_id(game))


def _game_repository(game):
    repository = Mock()
    repository.get_game.return_value = game
    return repository


def _club_provider(clubs):
    provider = Mock()
    provider.get_clubs_for_game.return_value = clubs
    return provider


def _game(
        current_matches,
        remaining_matches,
        competition_type=CompetitionType.CHAMPIONSHIP,
        standings=None,
):
    game = Mock()
    game.cmp = SimpleNamespace(current_matches=current_matches)
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
