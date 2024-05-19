
"""
Created Apr 26, 2019

@author montreal91
"""

from random import shuffle
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from core.club import Club
from core.competition import DdAbstractCompetition
from core.competition import ScheduleDay
from core.match import DdMatchParams
from core.match import DdMatchResult
from core.match import DdScheduledMatchStruct
from core.match import DdStandingsRowStruct


ClubPair = Tuple[int, int]
Score = Tuple[int, int]


class DdPlayoffParams(NamedTuple):
    """A passive class to store playoff parameters."""

    series_matches_pattern: Tuple[bool, ...]
    length: int
    gap_days: int
    match_params: DdMatchParams
    match_importance: int


class DdPlayoffSeries:
    """A class to describe inner logic of a playoff series."""

    _bottom_club_pk: int
    _params: DdPlayoffParams
    _results: List[DdMatchResult]
    _top_club_pk: int

    def __init__(self, params: DdPlayoffParams):
        self._params = params
        self._results = []

        self._top_club_pk = -1
        self._bottom_club_pk = -2

    @property
    def pair(self) -> ClubPair:
        """Returns pair of pks of contesting clubs."""

        return (self._top_club_pk, self._bottom_club_pk)

    @pair.setter
    def pair(self, val: ClubPair):
        """Sets pk of the top seed club and pk of the bottom seed club."""

        self._top_club_pk = val[0]
        self._bottom_club_pk = val[1]

    @property
    def score(self) -> Score:
        """Current score of the series."""

        s = {}
        s[self._top_club_pk] = 0
        s[self._bottom_club_pk] = 0

        for result in self._results:
            if result.home_sets > result.away_sets:
                s[result.home_pk] += 1
            else:
                s[result.away_pk] += 1
        return (
            s[self._top_club_pk],
            s[self._bottom_club_pk],
        )

    @property
    def winner(self) -> Optional[int]:
        """
        Winner of the series.

        If series is not over yet, returns None.
        """
        score = self.score
        to_win = len(self._params.series_matches_pattern) // 2
        if score[0] <= to_win and score[1] <= to_win:
            return None

        if score[0] > to_win:
            return self._top_club_pk
        return self._bottom_club_pk

    def AddResult(self, result: DdMatchResult):
        """
        Adds result to the series if correct.

        If result is incorrect, raises assertion error.
        """
        self._CheckResult(result)
        self._results.append(result)

    def _CheckResult(self, result: DdMatchResult):
        club_pks = self._top_club_pk, self._bottom_club_pk
        assert result.home_pk in club_pks, (
            f"Club #{result.home_pk} does not involved in this series."
        )
        assert result.away_pk in club_pks, (
            f"Club #{result.away_pk} does not involved in this series."
        )
        assert result.home_sets != result.away_sets, (
            "Number of sets won by opponents should not be equal."
        )


class DdPlayoffScheduledMatchStruct(DdScheduledMatchStruct):
    """Passive class for a scheduled playoff match."""

    series: Optional[DdPlayoffSeries]
    def __init__(self, home_pk: int, away_pk: int):
        super().__init__(home_pk, away_pk)
        self.series = None

    def SetSeries(self, series: DdPlayoffSeries):
        """Sets a link to playoff series to which this match belongs."""

        self.series = series


class DdPlayoff(DdAbstractCompetition):
    """A class to incapsulate playoff (cup) logic."""

    _LONG: Tuple[ClubPair, ...] = (
        (0, 8),
        (4, 9),
        (2, 10),
        (5, 11),
        (1, 12),
        (6, 13),
        (3, 14),
        (7, 15),
    )
    _SHORT: Tuple[ClubPair, ...] = (
        (0, 4),
        (2, 5),
        (1, 6),
        (3, 7),
    )

    _series: List[DdPlayoffSeries]
    _past_series: List[DdPlayoffSeries]

    def __init__(
        self,
        clubs: Dict[int, Club],
        params: DdPlayoffParams,
        standings: List[DdStandingsRowStruct],
    ):
        super().__init__(clubs, params)
        self._standings = sorted(
            standings,
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True,
        )
        self._round = 1
        self._series = []
        self._past_series = []
        self._participants = []
        self._MakeNewRound()

    @property
    def current_matches(self) ->  Optional[ScheduleDay]:
        res = super().current_matches
        if res is None:
            return res
        return [match for match in res if not match.is_played]

    @property
    def is_over(self):
        if len(self._series) > 1:
            return False
        last_day = self._day >= len(self._schedule)
        return self._series[0].winner is not None and last_day

    @property
    def match_importance(self) -> int:
        return self._params.match_importance * self._round

    @property
    def standings(self):
        result = []
        for series in self._past_series + self._series:
            res = dict(
                clubs=series.pair,
                score=series.score,
            )
            result.append(res)
        return result

    @property
    def title(self) -> str:
        return "Cup"

    def GetClubFame(self, club_pk):
        if club_pk not in self._participants:
            return 0

        def Apow(x, k):
            return k * 2 ** x

        wins = 0
        for series in self._past_series + self._series:
            if series.winner == club_pk:
                wins += 1

        return Apow(wins, 125)

    def Update(self):
        if self.is_over:
            return None

        if self.current_matches is None:
            self._day += 1
            if self._day == len(self._schedule) and not self.is_over:
                self._MakeNewRound()
            return None

        day_results = []
        for match in self.current_matches:
            processor = self._match_processor
            processor.SetMatchSurface(self._clubs[match.home_pk].surface)
            res = processor.ProcessMatch(
                self._clubs[match.home_pk].selected_player,
                self._clubs[match.away_pk].selected_player,
            )
            match.is_played = True

            res.home_pk = match.home_pk
            res.away_pk = match.away_pk
            day_results.append(res)
            match.series.AddResult(res)
        self._day += 1
        self._results.append(day_results)
        self._UpdateSchedule()
        return day_results

    @property
    def _remaining_days(self):
        for day in self._schedule[self._day:]:
            if day is not None:
                yield day

    def _GetClubPos(self, club_pk: int) -> int:
        for i, row in enumerate(self._standings):
            if row.club_pk == club_pk:
                return i
        return -1

    def _InsertGap(self):
        gaps = [None for _ in range(self._params.gap_days)]
        self._schedule.extend(gaps)

    def _MakeInitialRound(self):
        if self._params.length == len(self._LONG) * 2:
            predraw = _MakePreDraw(5)
            for top, bottom in self._LONG:
                series = DdPlayoffSeries(self._params)
                series.pair = (
                    self._standings[predraw[top]].club_pk,
                    self._standings[predraw[bottom]].club_pk,
                )
                self._series.append(series)
                self._participants.extend(series.pair)
        elif self._params.length == len(self._SHORT) * 2:
            predraw = _MakePreDraw(4)
            for top, bottom in self._SHORT:
                series = DdPlayoffSeries(self._params)
                series.pair = (
                    self._standings[predraw[top]].club_pk,
                    self._standings[predraw[bottom]].club_pk,
                )
                self._series.append(series)
                self._participants.extend(series.pair)

    def _MakeNewRound(self):
        if not self._series:
            self._MakeInitialRound()
        else:
            self._round += 1
            self._past_series.extend(self._series)
            new_round = []
            for i in range(0, len(self._series), 2):
                winner1 = self._series[i].winner
                winner2 = self._series[i + 1].winner
                pair = [
                    (winner1, self._GetClubPos(winner1)),
                    (winner2, self._GetClubPos(winner2)),
                ]
                pair.sort(key=lambda x: x[1])
                new_series = DdPlayoffSeries(self._params)
                new_series.pair = (pair[0][0], pair[1][0])
                new_round.append(new_series)
            self._series = new_round
        self._MakeSchedule()

    def _MakeSchedule(self):
        self._InsertGap()
        for i in self._params.series_matches_pattern:
            day = []
            for series in self._series:
                pair = series.pair
                if not i:
                    pair = (pair[1], pair[0])
                scheduled_match = DdPlayoffScheduledMatchStruct(*pair)
                scheduled_match.SetSeries(series)
                day.append(scheduled_match)
            day.reverse()
            self._schedule.append(day)
            self._InsertGap()

    def _UpdateSchedule(self):
        for day in self._remaining_days:
            for match in day:
                if match.series.winner is not None:
                    match.is_played = True


def _DrawParts(num: int):
    for i in range(num):
        if i in (0, 1):
            yield [i]
        else:
            yield list(range(2 ** (i - 1), 2 ** i))


def _MakePreDraw(i: int) -> List[int]:
    pre_draw: List[int] = []
    for chunk in _DrawParts(i):
        shuffle(chunk)
        pre_draw.extend(chunk)
    return pre_draw
