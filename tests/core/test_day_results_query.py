"""
Created August 28, 2026

@author montreal91
"""
from types import SimpleNamespace
from typing import Dict

from core.club import Club
from core.match_result import MatchResult
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
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
    return DayResultsQueryHandler(
        game_repository=_GameRepository(_Game(results)),
        club_provider=_ClubProvider({
            "manager": _Club("Manager Club"),
            "opponent": _Club("Opponent Club"),
            "home": _Club("Home Club"),
            "away": _Club("Away Club"),
        }),
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


class _GameRepository:
    def __init__(self, game):
        self._game = game

    def get_game(self, _game_id):
        return self._game


class _ClubProvider(TemporalClubProvider):
    def __init__(self, clubs):
        super().__init__()
        self._clubs = clubs

    def get_clubs_for_game(self, game_id: str) -> Dict[str, Club]:
        return self._clubs


class _Game:
    def __init__(self, results):
        self._results = results

    def get_context(self, _manager_club_id):
        return {
            "last_results": self._results,
        }


class _Club:
    def __init__(self, name):
        self.name = name
