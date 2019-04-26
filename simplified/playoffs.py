
"""
Created Apr 26, 2019

@author montreal91
"""

from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from simplified.club import DdClub
from simplified.match import DdMatchResult
from simplified.match import DdScheduledMatchStruct
from simplified.match import DdStandingsRowStruct
from simplified.parameters import DdGameParams


ClubPair = Tuple[DdClub, DdClub]
Score = Tuple[int, int]


class DdPlayoffSeriesParams(NamedTuple):
    contest_pattern: Tuple[bool, ...] = (
        True, True, False, False, True, False, True
    )
    gap_days: int = 1
    matches_to_win: int = 4
    # sets_to_win: int = 2


class DdPlayoffSeries:
    _club_pair: ClubPair
    _params: DdPlayoffSeriesParams

    _schedule: List[Optional[DdScheduledMatchStruct]]
    _results: List[DdMatchResult]

    def __init__(
        self,
        club_pair: Tuple[DdClub, DdClub],
        params: DdPlayoffSeriesParams,
    ):
        self._club_pair = club_pair
        self._params = params
        self._schedule = []

    @property
    def next_match(self) -> Optional[ClubPair]:
        if self._schedule:
            return self._schedule[-1]
        return None

    @property
    def score(self) -> Score:
        return 0, 0

    @property
    def winner(self) -> Optional[DdClub]:
        score = self.score
        to_win = self._params.matches_to_win
        if score[0] < to_win and score[1] < to_win:
            return None

        if score[0] == to_win:
            return self._club_pair[0]
        return self._club_pair[1]

    def AddResult(self, result: DdMatchResult):
        self._results.append(result)

    def PopMatch(self):
        if self._schedule:
            self._schedule.pop()

    def _MakeSchedule(self):
        def MakeGap():
            return [None for _ in range(self._params.gap_days)]

        self._schedule.extend(MakeGap)

        for cp in self._params.contest_pattern:
            pair = (0, 1) if cp else (1, 0)
            self._schedule.append(DdScheduledMatchStruct(*pair))
            self._schedule.extend(MakeGap())
        self._schedule.reverse()


class DdPlayoff:
    def __init__(
        self,
        clubs: Tuple[DdClub, ...],
        standings: List[DdStandingsRowStruct],
        params: DdGameParams
    ):
        self._clubs = clubs
        self._standings = sorted(
            standings,
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True,
        )
        self._params = params

        self._round = 0

    def _MakeInitialRound(self):
        pass

    @property
    def _playing_clubs(self):
        pass
