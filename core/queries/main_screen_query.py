"""
Created December 24, 2025

@author montreal91
"""
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Union

from core.competition import CompetitionType

_NO_PLAYOFF_CLUB_ID = -1
_NO_PLAYOFF_VALUE = "N/A"


class UpcomingMatch(NamedTuple):
    opponent_club_name: str
    home_away: str


class StandingRow(NamedTuple):
    pos: int
    club_id: int
    club_name: str
    sets: int
    games: int


class ChampionshipStandings(NamedTuple):
    rows: List[StandingRow]


class PlayoffSeriesRow(NamedTuple):
    round_number: int
    top_club_id: int
    top_club_name: str
    top_score: Union[int, str]
    bottom_club_id: int
    bottom_club_name: str
    bottom_score: Union[int, str]
    contains_manager_club: bool


class PlayoffStandings(NamedTuple):
    rows: List[PlayoffSeriesRow]


Standings = Union[ChampionshipStandings, PlayoffStandings]


class QueryResult(NamedTuple):
    day: str
    season: int
    balance: int
    club_name: str
    current_competition: str
    competition_type: CompetitionType
    has_matches: bool
    upcoming_match: Optional[UpcomingMatch]
    standings: Standings


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
                upcoming_match = UpcomingMatch(
                    opponent_club_name=opponent_club,
                    home_away="Home",
                )
            elif match.away_pk == manager_club_id:
                opponent_club = game.clubs[match.home_pk].name
                upcoming_match = UpcomingMatch(
                    opponent_club_name=opponent_club,
                    home_away="Away",
                )
            else:
                raise Exception("WTF Happened")

        if context["competition_type"] == CompetitionType.CHAMPIONSHIP:
            raw_standings = context.get("standings", [])
            res_standings = []
            clubs = self._club_repository.get_club_index(game_id)

            for pos, standing in enumerate(raw_standings):
                res_standings.append(StandingRow(
                    pos=pos + 1,
                    club_id=standing.club_id,
                    sets=standing.sets_won,
                    games=standing.games_won,
                    club_name=clubs[standing.club_id].name,
                ))

            standings = ChampionshipStandings(rows=res_standings)
        elif context["competition_type"] == CompetitionType.PLAY_OFFS:
            standings = _make_playoff_standings(
                raw_standings=context.get("standings", []),
                clubs=self._club_repository.get_club_index(game_id),
                manager_club_id=manager_club_id,
            )
        else:
            raise Exception("Unknown competition type")

        return QueryResult(
            day=context["day"],
            season=len(context["history"]),
            balance=context["balance"],
            club_name=context["club_name"],
            current_competition=context["competition"],
            competition_type=context["competition_type"],
            has_matches=context["has_matches"],
            upcoming_match=upcoming_match,
            standings=standings,
        )


def _make_playoff_standings(
        raw_standings,
        clubs,
        manager_club_id,
) -> PlayoffStandings:
    rows = []

    if not raw_standings:
        return PlayoffStandings(rows=rows)

    first_round_size = _largest_power_of_two(len(raw_standings))

    for round_number, standing in _playoff_rounds(raw_standings):
        top_club_id = standing["clubs"][0]
        bottom_club_id = standing["clubs"][1]

        rows.append(PlayoffSeriesRow(
            round_number=round_number,
            top_club_id=top_club_id,
            top_club_name=clubs[top_club_id].name,
            top_score=standing["score"][0],
            bottom_club_id=bottom_club_id,
            bottom_club_name=clubs[bottom_club_id].name,
            bottom_score=standing["score"][1],
            contains_manager_club=manager_club_id in standing["clubs"],
        ))

    rows.extend(_make_future_playoff_rounds(
        first_round_size=first_round_size,
        rendered_series=len(raw_standings),
    ))

    return PlayoffStandings(rows=rows)


def _make_future_playoff_rounds(first_round_size, rendered_series):
    rows = []
    round_number = 1
    round_size = first_round_size
    skipped_series = rendered_series

    while round_size > 0:
        if skipped_series >= round_size:
            skipped_series -= round_size
        else:
            for _ in range(round_size - skipped_series):
                rows.append(_make_empty_playoff_series(round_number))
            skipped_series = 0

        round_size //= 2
        round_number += 1

    return rows


def _make_empty_playoff_series(round_number):
    return PlayoffSeriesRow(
        round_number=round_number,
        top_club_id=_NO_PLAYOFF_CLUB_ID,
        top_club_name=_NO_PLAYOFF_VALUE,
        top_score=_NO_PLAYOFF_VALUE,
        bottom_club_id=_NO_PLAYOFF_CLUB_ID,
        bottom_club_name=_NO_PLAYOFF_VALUE,
        bottom_score=_NO_PLAYOFF_VALUE,
        contains_manager_club=False,
    )


def _playoff_rounds(raw_standings):
    if not raw_standings:
        return

    round_size = _largest_power_of_two(len(raw_standings))
    round_number = 1
    index = 0

    while index < len(raw_standings):
        for standing in raw_standings[index:index + round_size]:
            yield round_number, standing

        index += round_size
        round_size = max(round_size // 2, 1)
        round_number += 1


def _largest_power_of_two(value):
    res = 1
    while res * 2 <= value:
        res *= 2
    return res


def _get_match(competition, club_id):
    matches = competition.current_matches

    if matches is None:
        return None

    for match in matches:
        if match.home_pk == club_id or match.away_pk == club_id:
            return match

    return None
