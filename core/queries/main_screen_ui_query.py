"""
Created December 24, 2025

@author montreal91
"""
from typing import NamedTuple
from typing import Optional


class UpcomingMatch(NamedTuple):
    opponent_club_name: str


class QueryResult(NamedTuple):
    day: str
    season: int
    balance: int
    club_name: str
    current_competition: str
    has_matches: bool
    upcoming_match: Optional[UpcomingMatch]


class GameScreenGuiQueryHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        context = game.get_context(manager_club_id)

        match = _get_match(competition=game.competition, club_id=manager_club_id)

        upcoming_match = None

        if match:
            if match.home_pk == manager_club_id:
                opponent_club = game.clubs[match.away_pk].name
                upcoming_match = UpcomingMatch(opponent_club)
            elif match.away_pk == manager_club_id:
                opponent_club = game.clubs[match.home_pk].name
                upcoming_match = UpcomingMatch(opponent_club)
            else:
                raise Exception("WTF Happened")

        return QueryResult(
            day=context["day"],
            season=len(context["history"]),
            balance=context["balance"],
            club_name=context["club_name"],
            current_competition=context["competition"],
            has_matches=context["has_matches"],
            upcoming_match=upcoming_match,
        )

def _get_match(competition, club_id):
    matches = competition.current_matches

    if matches is None:
        return None

    for match in matches:
        if match.home_pk == club_id or match.away_pk == club_id:
            return match

    return None
