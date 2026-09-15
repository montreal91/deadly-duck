"""
Created December 26, 2025

@author montreal91
"""
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional

from core.club import Club
from core.match_result import MatchResult
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class DayResultsQuery:
    game_id: str
    manager_club_id: str


@dataclass(frozen=True)
class SingleMatchResult:
    home_club_id: str
    away_club_id: str
    home_club_name: str
    away_club_name: str
    home_player_name: str
    away_player_name: str
    score: str
    user_result: Optional[str]
    experience_gained: Optional[int]
    user_player_name: Optional[str]


@dataclass(frozen=True)
class DayResultsQueryResult:
    match_results_list: List[SingleMatchResult]


class DayResultsQueryHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider: TemporalClubProvider,
            competition_repository: CompetitionRepository,
            match_result_repository: MatchResultRepository,
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._match_result_repository = match_result_repository
        self._competition_repository = competition_repository

    def __call__(self, query: DayResultsQuery) -> DayResultsQueryResult:
        clubs = self._club_provider.get_clubs_for_game(query.game_id)
        results = []

        for result in self._get_last_results(query.game_id):
            results.append(_make_single_match_result(result, clubs, query.manager_club_id))

        return DayResultsQueryResult(match_results_list=results)

    def _get_last_results(self, game_id: str) -> List[MatchResult]:
        ongoing_competitions = self._competition_repository.get_ongoing_competitions_ids(game_id)
        last_results = []

        for c in ongoing_competitions:
            last_results.extend(self._match_result_repository.get_latest_results(game_id, c))

        return last_results


def _get_player_name(player_json):
    return (
        f"{player_json['first_name'][0]}. "
        f"{player_json['second_name'][0]}. "
        f"{player_json['last_name']}"
    )


def _make_single_match_result(
        result: MatchResult,
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
        user_result=_extract_user_result(result, manager_club_id),
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


def _extract_user_result(result, manager_club_id) -> Optional[str]:
    if result.home_pk == manager_club_id:
        return "Win" if result.home_sets > result.away_sets else "Loss"
    elif result.away_pk == manager_club_id:
        return "Win" if result.away_sets > result.home_sets else "Loss"

    return None


def _get_player_full_name(player_json):
    return f"{player_json['first_name']} {player_json['last_name']}"
