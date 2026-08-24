
"""
Created Apr 26, 2019

@author montreal91
"""

from random import shuffle
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from uuid import uuid4

from core.competition import AbstractCompetition
from core.competition import ScheduleDay
from core.match_engine import MatchParams
from core.match_result import MatchResult
from core.regular_championship import DdStandingsRowStruct
from core.scheduled_match import ScheduledMatch

ClubPair = Tuple[str, str]
BracketPair = Tuple[int, int]
Score = Tuple[int, int]


class DdPlayoffParams(NamedTuple):
    """A passive class to store playoff parameters."""

    series_matches_pattern: Tuple[bool, ...]
    length: int
    gap_days: int
    match_params: MatchParams
    match_importance: int


class DdPlayoffSeries:
    """A class to describe inner logic of a playoff series."""

    _bottom_club_pk: str
    _params: DdPlayoffParams
    _results: List[MatchResult]
    _series_id: str
    _top_club_pk: str

    def __init__(self, params: DdPlayoffParams, series_id=None):
        self._params = params
        self._results = []
        self._series_id = series_id or str(uuid4())

        self._top_club_pk = "__top_club_not_set__"
        self._bottom_club_pk = "__bottom_club_not_set__"

    @property
    def series_id(self):
        return self._series_id

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
    def winner(self) -> Optional[str]:
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

    def add_result(self, result: MatchResult):
        """
        Adds result to the series if correct.

        If result is incorrect, raises assertion error.
        """
        self._check_result(result)
        self._results.append(result)

    def _check_result(self, result: MatchResult):
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


class Playoff(AbstractCompetition):
    """A class to encapsulate playoff (cup) logic."""

    _LONG: Tuple[BracketPair, ...] = (
        (0, 8),
        (4, 9),
        (2, 10),
        (5, 11),
        (1, 12),
        (6, 13),
        (3, 14),
        (7, 15),
    )
    _SHORT: Tuple[BracketPair, ...] = (
        (0, 4),
        (2, 5),
        (1, 6),
        (3, 7),
    )

    _series: List[DdPlayoffSeries]
    _past_series: List[DdPlayoffSeries]

    def __init__(
        self,
        params: DdPlayoffParams,
        standings: List[DdStandingsRowStruct],
    ):
        super().__init__([row.club_id for row in standings], params)
        self._standings = sorted(
            standings,
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True,
        )
        self._round = 1
        self._series = []
        self._past_series = []
        self._participants = []
        self._series_by_id = {}
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
                seeds=(
                    self._get_club_seed(series.pair[0]),
                    self._get_club_seed(series.pair[1]),
                ),
            )
            result.append(res)
        return result

    @property
    def title(self) -> str:
        return "Katelyn Cup Playoffs"

    def get_club_fame(self, club_pk):
        if club_pk not in self._participants:
            return 0

        def Apow(x, k):
            return k * 2 ** x

        wins = 0
        for series in self._past_series + self._series:
            if series.winner == club_pk:
                wins += 1

        return Apow(wins, 125)

    def apply_results(self, results: List[MatchResult]):
        if self.is_over:
            assert not results, "Cannot apply results to finished competition."
            return

        self._validate_current_results(results)

        current_matches = self.current_matches or []
        matches_by_id = {
            match.match_id: match
            for match in current_matches
        }

        for result in results:
            match = matches_by_id[result.match_id]
            match.is_played = True
            series = self._series_by_id[match.playoff_series_id]
            series.add_result(result)

        self._day += 1
        if results:
            self._results.append(results)
        self._UpdateSchedule()

        if self._day == len(self._schedule) and not self.is_over:
            self._MakeNewRound()

    @property
    def _remaining_days(self):
        for day in self._schedule[self._day:]:
            if day is not None:
                yield day

    def _get_club_pos(self, club_pk: str) -> int:
        for i, row in enumerate(self._standings):
            if row.club_id == club_pk:
                return i
        return -1

    def _get_club_seed(self, club_pk: str) -> int:
        return self._get_club_pos(club_pk) + 1

    def _InsertGap(self):
        gaps = [None for _ in range(self._params.gap_days)]
        self._schedule.extend(gaps)

    def _MakeInitialRound(self):
        if self._params.length == len(self._LONG) * 2:
            predraw = _MakePreDraw(5)
            for top, bottom in self._LONG:
                series = DdPlayoffSeries(self._params)
                series.pair = (
                    self._standings[predraw[top]].club_id,
                    self._standings[predraw[bottom]].club_id,
                )
                self._series.append(series)
                self._series_by_id[series.series_id] = series
                self._participants.extend(series.pair)
        elif self._params.length == len(self._SHORT) * 2:
            predraw = _MakePreDraw(4)
            for top, bottom in self._SHORT:
                series = DdPlayoffSeries(self._params)
                series.pair = (
                    self._standings[predraw[top]].club_id,
                    self._standings[predraw[bottom]].club_id,
                )
                self._series.append(series)
                self._series_by_id[series.series_id] = series
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
                    (winner1, self._get_club_pos(winner1)),
                    (winner2, self._get_club_pos(winner2)),
                ]
                pair.sort(key=lambda x: x[1])
                new_series = DdPlayoffSeries(self._params)
                new_series.pair = (pair[0][0], pair[1][0])
                new_round.append(new_series)
                self._series_by_id[new_series.series_id] = new_series
            self._series = new_round
        self._make_schedule()

    def _make_schedule(self):
        self._InsertGap()
        for i in self._params.series_matches_pattern:
            day = []
            for series in self._series:
                pair = series.pair
                if not i:
                    pair = (pair[1], pair[0])
                scheduled_match = ScheduledMatch(
                    pair[0],
                    pair[1],
                    playoff_series_id=series.series_id,
                )
                day.append(scheduled_match)
            day.reverse()
            self._schedule.append(day)
            self._InsertGap()

    def _UpdateSchedule(self):
        for day in self._remaining_days:
            for match in day:
                series = self._series_by_id[match.playoff_series_id]
                if series.winner is not None:
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
