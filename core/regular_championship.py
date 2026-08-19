
"""
Created May 20, 2019

@author montreal91
"""
from random import shuffle
from typing import Dict
from typing import Generator
from typing import List
from typing import NamedTuple
from typing import Optional

from core.competition import DdAbstractCompetition
from core.competition import ScheduleDay
from core.match import DdMatchParams
from core.match import DdMatchResult
from core.match import DdScheduledMatchStruct
from core.match import DdStandingsRowStruct


class ChampionshipParams(NamedTuple):
    """A passive class to store regular championship parameters."""

    match_params: DdMatchParams
    recovery_day: int
    rounds: int
    match_importance: int


class RegularChampionship(DdAbstractCompetition):
    """A class to encapsulate logic of a regular championship."""

    _params: ChampionshipParams
    _results: List[List[DdMatchResult]]
    _standings: Dict[int, List[DdStandingsRowStruct]]

    def __init__(self, clubs, params):
        super().__init__(clubs, params)
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

        # results = [DdStandingsRowStruct(i) for i in self._clubs]
        results = {}
        for club_id in self._clubs:
            results[club_id] = DdStandingsRowStruct(club_id=club_id)

        for day in self._results:
            for match in day:
                results[match.home_pk].sets_won += match.home_sets
                results[match.home_pk].games_won += match.home_games

                results[match.away_pk].sets_won += match.away_sets
                results[match.away_pk].games_won += match.away_games

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

    def update(self) -> Optional[List[DdMatchResult]]:
        if self.current_matches is None:
            self._day += 1
            return None
        day_results = []
        for match in self.current_matches:
            processor = self._match_processor
            res = processor.process_match(
                self._clubs[match.home_pk].selected_player,
                self._clubs[match.away_pk].selected_player,
            )
            match.is_played = True

            res.home_pk = match.home_pk
            res.away_pk = match.away_pk
            day_results.append(res)
        self._day += 1
        self._results.append(day_results)
        return day_results

    def _make_full_schedule(self, pk_list: List[str]):
        # Alias to shorten length of code lines
        _Match = DdScheduledMatchStruct

        def mirror_day(matches: List[DdScheduledMatchStruct]):
            return [_Match(m.away_pk, m.home_pk) for m in matches]

        def copy_day(matches):
            return [_Match(m.home_pk, m.away_pk) for m in matches]

        def compose_days(matches: List[DdScheduledMatchStruct], num: int):
            res = []
            for _ in range(num // 2):
                res.append(copy_day(matches))
            for _ in range(num // 2):
                res.append(mirror_day(matches))
            return res

        basic_schedule = _make_basic_schedule(pk_list)

        res: List[ScheduleDay] = []
        in_div = self._params.rounds
        ex_div = self._params.rounds

        for i, match in enumerate(basic_schedule):
            if i % 2 == 0:
                res.extend(compose_days(match, ex_div))
            else:
                res.extend(compose_days(match, in_div))
        return res

    def _make_schedule(self):
        pk_list = [cid for cid in self._clubs]
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

            self._schedule.append(days[done])
            done += 1

        self._schedule.append(None)


def _make_basic_schedule(pk_list: List[str]):
    def make_pairs(lst: List[str]) -> ScheduleDay:
        num = len(lst) - 1
        mid = len(lst) // 2
        return [
            DdScheduledMatchStruct(lst[i], lst[num-i]) for i in range(mid)
        ]

    def shift(lst: List[str], num: int) -> List[str]:
        if num == 0:
            return list(lst)
        return [lst[0]] + lst[-num:] + lst[1:-num]

    def shift_gen(lst: List[str]) -> Generator[List[str], None, None]:
        for i in range(len(lst) - 1):
            yield shift(lst, i)

    return [make_pairs(l) for l in shift_gen(pk_list)]
