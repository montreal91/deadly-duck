"""
Created December 24, 2025

@author montreal91
"""
from typing import (
    NamedTuple,
    List
)
from typing import Optional


class UpcomingMatch(NamedTuple):
    opponent_club_name: str


class StandingRow(NamedTuple):
    pos: int
    club_id: int
    club_name: str
    sets: int
    games: int


class QueryResult(NamedTuple):
    day: str
    season: int
    balance: int
    club_name: str
    current_competition: str
    has_matches: bool
    upcoming_match: Optional[UpcomingMatch]
    standings: List[StandingRow]


class GameScreenGuiQueryHandler:
    def __init__(self, game_repository, club_repository):
        self._game_repository = game_repository
        self._club_repository = club_repository

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

        raw_standings = context.get("standings", [])
        res_standings = []
        clubs = self._club_repository.get_club_index(game_id)

        for pos, standing in enumerate(raw_standings):
            res_standings.append(StandingRow(
                pos=pos + 1,
                club_id=standing.club_pk,
                sets=standing.sets_won,
                games=standing.games_won,
                club_name=clubs[standing.club_pk].name,
            ))

        return QueryResult(
            day=context["day"],
            season=len(context["history"]),
            balance=context["balance"],
            club_name=context["club_name"],
            current_competition=context["competition"],
            has_matches=context["has_matches"],
            upcoming_match=upcoming_match,
            standings=res_standings,
        )


def _get_match(competition, club_id):
    matches = competition.current_matches

    if matches is None:
        return None

    for match in matches:
        if match.home_pk == club_id or match.away_pk == club_id:
            return match

    return None
