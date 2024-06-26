
"""
Created May 20, 2019

@author montreal91
"""

from copy import copy
from itertools import chain
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional

from core.club import Club
from core.match import DdMatchProcessor
from core.match import DdMatchResult
from core.match import DdScheduledMatchStruct


ScheduleDay = List[DdScheduledMatchStruct]


class DdAbstractCompetition:
    """Abstract competition class."""

    _clubs: Dict[int, Club]
    _schedule: List[Optional[ScheduleDay]]
    _day: int
    _params: Any
    _results: List[List[DdMatchResult]]

    def __init__(self, clubs: Dict[int, Club], params: Any):
        self._clubs = clubs
        self._day = 0
        self._params = params
        self._results = []
        self._schedule = []

    @property
    def current_matches(self) -> Optional[ScheduleDay]:
        """List of current matches."""

        if self._day < len(self._schedule):
            return self._schedule[self._day]
        return None

    @property
    def day(self):
        """Current day of a competition."""

        return self._day

    @property
    def is_over(self) -> bool:
        """Checks if competition is over"""

    @property
    def match_importance(self) -> int:
        """Returns an importance factor of current matches."""

    @property
    def results_(self) -> Generator[List[DdMatchResult], None, None]:
        """
        List of match results.

        Actually, this method is present here for testing purposes and should
        not be used for production.
        """
        for match in chain(*self._results):
            yield copy(match)

    @property
    def standings(self) -> List[Any]:
        """List of current standings."""

    @property
    def title(self) -> str:
        """Title of the competition."""

    def GetClubSchedule(self, club_pk: int) -> List[DdScheduledMatchStruct]:
        """List of matches scheduled for a club."""

        schedule = []
        for day in self._schedule:
            if day is None:
                continue
            for match in day:
                if match.is_played:
                    continue
                if club_pk in (match.home_pk, match.away_pk):
                    schedule.append(match)
        return schedule

    def GetClubFame(self, club_pk: int) -> int:
        """Fame earned by club in the competition."""

    def Update(self) -> Optional[List[DdMatchResult]]:
        """Updates the state of the competition."""

    @property
    def _match_processor(self) -> DdMatchProcessor:
        return DdMatchProcessor(self._params.match_params)

    def _MakeSchedule(self):
        pass
