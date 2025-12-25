"""
Created December 26, 2025

@author montreal91
"""
from typing import NamedTuple, List


class DayResultsQuery:
    def __init__(self, game_id, manager_club_id):
        self.game_id = game_id
        self.manager_club_id = manager_club_id


class SingleMatchResult(NamedTuple):
    home_club_id: int
    away_club_id: int
    home_club_name: str
    away_club_name: str
    home_player_name: str
    away_player_name: str
    score: str


class DayResultsQueryResult(NamedTuple):
    match_results_list: List[SingleMatchResult]
    # def __init__(self, match_results_list):
    #     self.match_results_list = match_results_list


class DayResultsQueryHandler:
    def __init__(self, game_repository, club_repository):
        self._game_repository = game_repository
        self._club_repository = club_repository

    def __call__(self, query):
        print("HUGS: Day results are queried.")
        game = self._game_repository.get_game(query.game_id).get_context(query.manager_club_id)
        clubs = self._club_repository.get_club_index(query.game_id)

        last_results = game["last_results"]
        results = []
        for result in last_results:
            results.append(SingleMatchResult(
                home_club_id=result.home_pk,
                away_club_id=result.away_pk,
                home_club_name=clubs[result.home_pk].name,
                away_club_name=clubs[result.away_pk].name,
                home_player_name=_get_player_name(result.home_player_snapshot),
                away_player_name=_get_player_name(result.away_player_snapshot),
                score=result.full_score,
            ))

        return DayResultsQueryResult(match_results_list=results)


def _get_player_name(player_json):
    return (
        f"{player_json['first_name'][0]}. "
        f"{player_json['second_name'][0]}. "
        f"{player_json['last_name']}"
    )
