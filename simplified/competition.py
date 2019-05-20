
"""
Created May 20, 2019

@author montreal91
"""

from typing import Any
from typing import List
from typing import Optional

from simplified.club import DdClub
from simplified.match import DdMatchProcessor
from simplified.match import DdMatchResult
from simplified.match import DdScheduledMatchStruct


ScheduleDay = List[DdScheduledMatchStruct]


class DdAbstractCompetition:
    """Abstract competition class."""

    _clubs: List[DdClub]
    _schedule: List[Optional[ScheduleDay]]
    _day: int
    _params: Any

    def __init__(self, clubs: List[DdClub], params: Any):
        self._clubs = clubs
        self._day = 0
        self._params = params
        self._schedule = []
        self._MakeSchedule()

    @property
    def current_matches(self) -> Optional[ScheduleDay]:
        """List of current matches."""

        return self._schedule[self._day]

    @property
    def day(self):
        """Current day of a competition."""

        return self._day

    @property
    def is_over(self) -> bool:
        """Checks if competition is over"""

    @property
    def standings(self) -> List[Any]:
        """List of current standings."""

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

    def Update(self) -> Optional[List[DdMatchResult]]:
        """Updates the state of the competition."""

    @property
    def _match_processor(self) -> DdMatchProcessor:
        pass

    def _MakeSchedule(self):
        pass
