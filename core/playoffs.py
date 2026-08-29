
"""
Created Apr 26, 2019

@author montreal91
"""

from random import shuffle
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union
from uuid import uuid4

from core.competition import AbstractCompetition
from core.competition import ScheduleDay
from core.match_engine import MatchParams
from core.match_result import MatchResult
from core.scheduled_match import ScheduledMatch

ClubPair = Tuple[Optional[str], Optional[str]]
BracketPair = Tuple[int, int]
Score = Tuple[Union[int, str], Union[int, str]]


class DdPlayoffParams(NamedTuple):
    """A passive class to store playoff parameters."""

    series_matches_pattern: Tuple[bool, ...]
    length: int
    gap_days: int
    match_params: MatchParams
    match_importance: int


class PlayoffSeed(NamedTuple):
    """A seeded playoff participant."""

    club_id: str
    seed: int


class DdPlayoffSeries:
    """A class to describe inner logic of a playoff series."""

    _bottom_club_pk: Optional[str]
    _params: DdPlayoffParams
    _results: List[MatchResult]
    _round_number: int
    _series_id: str
    _top_club_pk: Optional[str]

    def __init__(self, params: DdPlayoffParams, series_id=None, round_number=1):
        self._params = params
        self._results = []
        self._round_number = round_number
        self._series_id = series_id or str(uuid4())

        self._top_club_pk = "__top_club_not_set__"
        self._bottom_club_pk = "__bottom_club_not_set__"

    @property
    def series_id(self):
        return self._series_id

    @property
    def round_number(self):
        return self._round_number

    @property
    def pair(self) -> ClubPair:
        """Returns a pair of pks of contesting clubs."""

        return self._top_club_pk, self._bottom_club_pk

    @pair.setter
    def pair(self, val: ClubPair):
        """Sets pk of the top seed club and pk of the bottom seed club."""

        assert val[0] is not None or val[1] is not None, (
            "Playoff series should have at least one club."
        )
        self._top_club_pk = val[0]
        self._bottom_club_pk = val[1]

    @property
    def score(self) -> Score:
        """Current score of the series."""

        if self._top_club_pk is None or self._bottom_club_pk is None:
            return "", ""

        s = {
            self._top_club_pk: 0,
            self._bottom_club_pk: 0
        }

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
        if self._top_club_pk is None:
            return self._bottom_club_pk
        if self._bottom_club_pk is None:
            return self._top_club_pk

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
        seeds: List[PlayoffSeed],
    ):
        super().__init__([seed.club_id for seed in seeds], params)
        assert len(seeds) == params.length, (
            "Playoff seeds should match playoff length."
        )
        self._seeds = sorted(seeds, key=lambda seed: seed.seed)
        self._seed_by_club_id = {
            seed.club_id: seed.seed
            for seed in self._seeds
        }
        self._round = 1
        self._series = []
        self._past_series = []
        self._participants = [seed.club_id for seed in self._seeds]
        self._series_by_id = {}
        self._make_new_round()

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
                round_number=series.round_number,
            )
            result.append(res)
        return result

    @property
    def title(self) -> str:
        return "Katelyn Cup Playoffs"

    def get_club_fame(self, club_pk):
        if club_pk not in self._participants:
            return 0

        def a_pow(x, k):
            return k * 2 ** x

        wins = 0
        for series in self._past_series + self._series:
            if series.winner == club_pk:
                wins += 1

        return a_pow(wins, 125)

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
        self._update_schedule()

        if self._day == len(self._schedule) and not self.is_over:
            self._make_new_round()

    @property
    def _remaining_days(self):
        for day in self._schedule[self._day:]:
            if day is not None:
                yield day

    def _get_club_pos(self, club_pk: str) -> int:
        for i, seed in enumerate(self._seeds):
            if seed.club_id == club_pk:
                return i
        return -1

    def _get_club_seed(self, club_pk: Optional[str]) -> Union[int, str]:
        if club_pk is None:
            return ""
        return self._seed_by_club_id[club_pk]

    def _insert_gap(self):
        gaps = [None for _ in range(self._params.gap_days)]
        self._schedule.extend(gaps)

    def _make_initial_round(self):
        if self._params.length == 12:
            self._make_preliminary_round()
        elif self._params.length == len(self._LONG) * 2:
            self._make_round_from_bracket_pairs(
                bracket_pairs=self._LONG,
                predraw=_make_pre_draw(5),
            )
        elif self._params.length == len(self._SHORT) * 2:
            self._make_round_from_bracket_pairs(
                bracket_pairs=self._SHORT,
                predraw=_make_pre_draw(4),
            )
        else:
            raise AssertionError("Unsupported playoff length.")

    def _make_preliminary_round(self):
        protected_paths = [
            self._seeds[index]
            for index in (0, 2, 1, 3)
        ]
        upper_challengers = self._seeds[4:8]
        lower_challengers = self._seeds[8:12]

        shuffle(upper_challengers)
        shuffle(lower_challengers)

        challenger_paths = list(zip(upper_challengers, lower_challengers))
        shuffle(challenger_paths)

        for protected_seed, challenger_path in zip(
                protected_paths,
                challenger_paths,
        ):
            top_seed, bottom_seed = challenger_path
            self._add_series(protected_seed.club_id, None)
            self._add_series(top_seed.club_id, bottom_seed.club_id)

    def _make_round_from_bracket_pairs(
            self,
            bracket_pairs: Tuple[BracketPair, ...],
            predraw: List[int],
    ):
        for top, bottom in bracket_pairs:
            self._add_series(
                self._seeds[predraw[top]].club_id,
                self._seeds[predraw[bottom]].club_id,
            )

    def _add_series(
            self,
            top_club_id: Optional[str],
            bottom_club_id: Optional[str],
    ):
        series = self._create_series(top_club_id, bottom_club_id)
        self._series.append(series)
        self._series_by_id[series.series_id] = series

    def _create_series(
            self,
            top_club_id: Optional[str],
            bottom_club_id: Optional[str],
    ):
        series = DdPlayoffSeries(self._params, round_number=self._round)
        series.pair = (top_club_id, bottom_club_id)
        return series

    def _make_new_round(self):
        if not self._series:
            self._make_initial_round()
        else:
            self._round += 1
            self._past_series.extend(self._series)
            new_round = []
            winners = self._series_winners()
            for i in range(0, len(winners), 2):
                winner1 = winners[i]
                winner2 = winners[i + 1]
                pair = [
                    (winner1, self._get_club_pos(winner1)),
                    (winner2, self._get_club_pos(winner2)),
                ]
                pair.sort(key=lambda x: x[1])
                new_series = self._create_series(pair[0][0], pair[1][0])
                new_round.append(new_series)
                self._series_by_id[new_series.series_id] = new_series
            self._series = new_round
        self._make_schedule()

    def _series_winners(self) -> List[str]:
        winners = []
        for series in self._series:
            winner = series.winner
            assert winner is not None, (
                "Cannot make next playoff round before all series are over."
            )
            winners.append(winner)
        return winners

    def _make_schedule(self):
        self._insert_gap()
        for i in self._params.series_matches_pattern:
            day = []
            for series in self._series:
                if series.winner is not None:
                    continue
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
            self._insert_gap()

    def _update_schedule(self):
        for day in self._remaining_days:
            for match in day:
                series = self._series_by_id[match.playoff_series_id]
                if series.winner is not None:
                    match.is_played = True


def _draw_parts(num: int):
    for i in range(num):
        if i in (0, 1):
            yield [i]
        else:
            yield list(range(2 ** (i - 1), 2 ** i))


def _make_pre_draw(i: int) -> List[int]:
    pre_draw: List[int] = []
    for chunk in _draw_parts(i):
        shuffle(chunk)
        pre_draw.extend(chunk)
    return pre_draw
