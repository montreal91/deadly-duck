"""
Created August 28, 2026

@author montreal91
"""
from unittest.mock import Mock

from core.match_result import MatchResult
from core.queries.day_results_query import DayResultsQuery
from core.queries.day_results_query import DayResultsQueryHandler
from core.set_result import DdSetStatuses
from core.set_result import SetResult


def test_day_results_query_marks_home_manager_win():
    result = _match_result("manager", "opponent", [(6, 4), (6, 4)])
    handler = _handler([result])

    query_result = handler(DayResultsQuery("game", "manager"))

    assert query_result.match_results_list[0].user_result == "Win"


def test_day_results_query_marks_away_manager_loss():
    result = _match_result("opponent", "manager", [(6, 4), (6, 4)])
    handler = _handler([result])

    query_result = handler(DayResultsQuery("game", "manager"))

    assert query_result.match_results_list[0].user_result == "Loss"


def test_day_results_query_omits_user_result_for_other_clubs():
    result = _match_result("home", "away", [(6, 4), (6, 4)])
    handler = _handler([result])

    query_result = handler(DayResultsQuery("game", "manager"))

    assert query_result.match_results_list[0].user_result is None


def _handler(results):
    game = Mock()
    game.get_context.return_value = {"last_results": results}

    game_repository = Mock()
    game_repository.get_game.return_value = game

    club_provider = Mock()
    club_provider.get_clubs_for_game.return_value = {
        "manager": _club("Manager Club"),
        "opponent": _club("Opponent Club"),
        "home": _club("Home Club"),
        "away": _club("Away Club"),
    }

    return DayResultsQueryHandler(
        game_repository=game_repository,
        club_provider=club_provider,
    )


def _match_result(home_pk, away_pk, set_scores):
    result = MatchResult()
    result.home_pk = home_pk
    result.away_pk = away_pk
    result.home_player_snapshot = _player("Home")
    result.away_player_snapshot = _player("Away")
    for home_games, away_games in set_scores:
        result.AddSetResult(SetResult(
            home_games=home_games,
            away_games=away_games,
            set_status=DdSetStatuses.REGULAR,
        ))
    return result


def _player(first_name):
    return {
        "first_name": first_name,
        "second_name": "Second",
        "last_name": "Player",
    }


def _club(name):
    club = Mock()
    club.name = name
    return club
