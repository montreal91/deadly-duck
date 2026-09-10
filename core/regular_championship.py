
"""
Created May 20, 2019

@author montreal91
"""
from dataclasses import dataclass
from random import shuffle
from typing import Dict
from typing import Generator
from typing import List
from typing import NamedTuple

from core.competition import AbstractCompetition
from core.competition import ScheduleDay
from core.match_engine import MatchParams
from core.match_result import MatchResult
from core.scheduled_match import ScheduledMatch


class ChampionshipParams(NamedTuple):
    """A passive class to store regular championship parameters."""

    match_params: MatchParams
    recovery_day: int
    rounds: int
    match_importance: int

class DdStandingsRowStruct:
    """Passive class for a row in standings."""

    def __init__(self, club_id):
        self.club_id = club_id
        self.matches_played = 0
        self.sets_won = 0
        self.games_won = 0


@dataclass
class _MatchPair:
    home_pk: str
    away_pk: str


class RegularChampionship(AbstractCompetition):
    """A class to encapsulate logic of a regular championship."""

    _params: ChampionshipParams
    _results: List[List[MatchResult]]
    _standings: Dict[int, List[DdStandingsRowStruct]]

    def __init__(self, club_ids, params):
        super().__init__(club_ids, params)
        self._make_schedule()

        self._standings = {}

    @property
    def is_over(self) -> bool:
        return self._day >= len(self._schedule)

    @property
    def match_importance(self) -> int:
        return self._params.match_importance

    @property
    def standings(self) -> List[DdStandingsRowStruct]:
        if self._day in self._standings:
            return self._standings[self._day]

        results = {}
        for club_id in self._club_ids:
            results[club_id] = DdStandingsRowStruct(club_id=club_id)

        for day in self._results:
            for match in day:
                results[match.home_pk].sets_won += match.home_sets
                results[match.home_pk].games_won += match.home_games

                results[match.away_pk].sets_won += match.away_sets
                results[match.away_pk].games_won += match.away_games

                results[match.home_pk].matches_played += 1
                results[match.away_pk].matches_played += 1

        results_list = [results[cid] for cid in results]

        self._standings[self._day] = sorted(
            results_list,
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True
        )

        return self._standings[self._day]

    @property
    def title(self):
        return "Regular Season"

    def get_club_fame(self, club_pk):
        for pos, row in enumerate(self.standings):
            if row.club_id == club_pk and pos == 0:
                return 500

        return 0

    def apply_results(self, results: List[MatchResult]):
        self._validate_current_results(results)

        for match in self.current_matches or []:
            match.is_played = True

        self._day += 1
        if results:
            self._results.append(results)

    def _make_match(self, home_id: str, away_id: str, schedule_day: int) -> ScheduledMatch:
        return ScheduledMatch(
            home_pk=home_id,
            away_pk=away_id,
            competition_id=self.competition_id,
            schedule_day=schedule_day
        )

    def _make_full_schedule(self, pk_list: List[str]):
        def mirror_day(matches: List[_MatchPair]) -> List[_MatchPair]:
            return [_MatchPair(m.away_pk, m.home_pk) for m in matches]

        def copy_day(matches: List[_MatchPair]) -> List[_MatchPair]:
            return [_MatchPair(m.home_pk, m.away_pk) for m in matches]

        def compose_days(matches: List[_MatchPair], num: int) -> List[List[_MatchPair]]:
            d_res = []
            for _ in range(num // 2):
                d_res.append(copy_day(matches))
            for _ in range(num // 2):
                d_res.append(mirror_day(matches))
            return d_res

        basic_schedule = _make_basic_schedule(pk_list)

        res: List[List[_MatchPair]] = []
        in_div = self._params.rounds
        ex_div = self._params.rounds

        for i, match in enumerate(basic_schedule):
            if i % 2 == 0:
                res.extend(compose_days(match, ex_div))
            else:
                res.extend(compose_days(match, in_div))
        return res

    def _make_schedule(self):
        pk_list = list(self._club_ids)
        shuffle(pk_list)
        days = self._make_full_schedule(pk_list)
        shuffle(days)

        day = -1
        done = 0
        while done < len(days):
            day += 1
            if day % self._params.recovery_day == 0:
                self._schedule.append(None)
                continue

            self._schedule.append(
                self._make_new_day(matches=days[done], day=day)
                # days[done]
            )
            done += 1

        self._schedule.append(None)

    def _make_new_day(self, day: int, matches: List[_MatchPair]) -> List[ScheduledMatch]:
        return [self._make_match(m.home_pk, m.away_pk, day) for m in matches]


def _make_basic_schedule(pk_list: List[str]) -> List[List[_MatchPair]]:
    def make_pairs(lst: List[str]) -> List[_MatchPair]:
        num = len(lst) - 1
        mid = len(lst) // 2
        return [
            _MatchPair(lst[i], lst[num - i]) for i in range(mid)
        ]

    def shift(lst: List[str], num: int) -> List[str]:
        if num == 0:
            return list(lst)
        return [lst[0]] + lst[-num:] + lst[1:-num]

    def shift_gen(lst: List[str]) -> Generator[List[str], None, None]:
        for i in range(len(lst) - 1):
            yield shift(lst, i)

    return [make_pairs(l) for l in shift_gen(pk_list)]
