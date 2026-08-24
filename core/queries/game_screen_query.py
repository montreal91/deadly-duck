"""
Created December 24, 2025

@author montreal91
"""
from datetime import datetime
from datetime import timedelta
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Union

from core.competition import CompetitionType
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_NO_PLAYOFF_CLUB_ID = ""
_NO_PLAYOFF_VALUE = "N/A"
_NO_PLAYOFF_SCORE = ""


class UpcomingMatch(NamedTuple):
    opponent_club_name: str
    home_away: str


class UpcomingDay(NamedTuple):
    day: str
    match: Optional[UpcomingMatch]


class StandingRow(NamedTuple):
    pos: int
    club_id: str
    club_name: str
    matches: int
    sets: int
    games: int


class ChampionshipStandings(NamedTuple):
    rows: List[StandingRow]


class PlayoffSeriesRow(NamedTuple):
    round_number: int
    top_club_id: str
    top_club_name: str
    top_score: Union[int, str]
    bottom_club_id: str
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
    level_ups_count: int
    upcoming_match: Optional[UpcomingMatch]
    standings: Standings
    upcoming_days: List[UpcomingDay]


class GameScreenGuiQueryHandler:
    _club_provider: TemporalClubProvider

    def __init__(self, game_repository, club_provider: TemporalClubProvider):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        context = game.get_context(manager_club_id)
        clubs = self._club_provider.get_clubs_for_game(game_id)

        match = _get_match(competition=game.competition, club_id=manager_club_id)
        upcoming_match = _make_upcoming_match(match, clubs, manager_club_id)

        if context["competition_type"] == CompetitionType.CHAMPIONSHIP:
            raw_standings = context.get("standings", [])
            res_standings = []

            for pos, standing in enumerate(raw_standings):
                res_standings.append(StandingRow(
                    pos=pos + 1,
                    club_id=standing.club_id,
                    club_name=clubs[standing.club_id].name,
                    matches=standing.matches_played,
                    sets=standing.sets_won,
                    games=standing.games_won,
                ))

            standings = ChampionshipStandings(rows=res_standings)
        elif context["competition_type"] == CompetitionType.PLAY_OFFS:
            standings = _make_playoff_standings(
                raw_standings=context.get("standings", []),
                clubs=clubs,
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
            level_ups_count=_count_players_with_unspent_skill_points(
                clubs,
                manager_club_id,
            ),
            upcoming_match=upcoming_match,
            standings=standings,
            upcoming_days=_make_upcoming_days(
                raw_days=context["remaining_matches"],
                clubs=clubs,
                manager_club_id=manager_club_id,
                first_day=context["day"],
            ),
        )


def _count_players_with_unspent_skill_points(clubs, manager_club_id) -> int:
    club = clubs.get(manager_club_id)

    if club is None:
        return 0

    return sum(
        int(slot.player.skill_points > 0)
        for slot in club.players
    )


def _make_upcoming_days(
        raw_days,
        clubs,
        manager_club_id,
        first_day,
) -> List[UpcomingDay]:
    current_day = datetime.strptime(first_day, "%Y-%b-%d").date()

    return [
        UpcomingDay(
            day=(current_day + timedelta(days=day_index)).strftime("%Y-%b-%d"),
            match=_make_upcoming_match(match, clubs, manager_club_id),
        )
        for day_index, match in enumerate(raw_days)
    ]


def _make_upcoming_match(match, clubs, manager_club_id) -> Optional[UpcomingMatch]:
    if match is None:
        return None

    if match.home_pk == manager_club_id:
        opponent_club = clubs[match.away_pk].name
        return UpcomingMatch(
            opponent_club_name=opponent_club,
            home_away="Home",
        )

    if match.away_pk == manager_club_id:
        opponent_club = clubs[match.home_pk].name
        return UpcomingMatch(
            opponent_club_name=opponent_club,
            home_away="Away",
        )

    raise Exception("Match does not contain manager club.")


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
        top_score=_NO_PLAYOFF_SCORE,
        bottom_club_id=_NO_PLAYOFF_CLUB_ID,
        bottom_club_name=_NO_PLAYOFF_VALUE,
        bottom_score=_NO_PLAYOFF_SCORE,
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
