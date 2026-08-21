"""
Created December 26, 2025

@author montreal91
"""
from typing import List, Dict
from typing import Optional
from typing import NamedTuple

from core.club import Club
from core.match import DdMatchResult
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


class DayResultsQuery:
    def __init__(self, game_id, manager_club_id):
        self.game_id = game_id
        self.manager_club_id = manager_club_id


class SingleMatchResult(NamedTuple):
    home_club_id: str
    away_club_id: str
    home_club_name: str
    away_club_name: str
    home_player_name: str
    away_player_name: str
    score: str
    experience_gained: Optional[int]
    user_player_name: Optional[str]


class DayResultsQueryResult(NamedTuple):
    match_results_list: List[SingleMatchResult]


class DayResultsQueryHandler:
    def __init__(self, game_repository, club_provider: TemporalClubProvider):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(self, query):
        game_context = self._game_repository.get_game(query.game_id).get_context(query.manager_club_id)
        clubs = self._club_provider.get_clubs_for_game(query.game_id)

        last_results = game_context["last_results"]
        results = []
        for result in last_results:
            results.append(_make_single_match_result(result, clubs, query.manager_club_id))

        return DayResultsQueryResult(match_results_list=results)


def _get_player_name(player_json):
    return (
        f"{player_json['first_name'][0]}. "
        f"{player_json['second_name'][0]}. "
        f"{player_json['last_name']}"
    )


def _make_single_match_result(
        result: DdMatchResult,
        clubs: Dict[str, Club],
        manager_club_id: str
) -> SingleMatchResult:
    return SingleMatchResult(
        home_club_id=result.home_pk,
        away_club_id=result.away_pk,
        home_club_name=clubs[result.home_pk].name,
        away_club_name=clubs[result.away_pk].name,
        home_player_name=_get_player_name(result.home_player_snapshot),
        away_player_name=_get_player_name(result.away_player_snapshot),
        score=result.full_score,
        experience_gained=_extract_exp(result, manager_club_id),
        user_player_name=_extract_user_player_name(result, manager_club_id),
    )


def _extract_exp(result, manager_club_id) -> Optional[int]:
    if result.home_pk == manager_club_id:
        return result.home_exp
    elif result.away_pk == manager_club_id:
        return result.away_exp

    return None


def _extract_user_player_name(result, manager_club_id) -> Optional[str]:
    if result.home_pk == manager_club_id:
        return _get_player_full_name(result.home_player_snapshot)
    elif result.away_pk == manager_club_id:
        return _get_player_full_name(result.away_player_snapshot)

    return None


def _get_player_full_name(player_json):
    return f"{player_json['first_name']} {player_json['last_name']}"
