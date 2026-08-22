
"""
Created May 20, 2019

@author montreal91
"""
from copy import copy
from enum import Enum
from itertools import chain
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from uuid import uuid4

from core.club import Club
from core.match_engine import MatchEngine
from core.match_result import MatchResult
from core.scheduled_match import ScheduledMatch

ScheduleDay = List[ScheduledMatch]


class CompetitionType(Enum):
    CHAMPIONSHIP = "championship"
    PLAY_OFFS = "play_offs"


class AbstractCompetition:
    """Abstract competition class."""

    _clubs: Dict[str, Club]
    _competition_id: str
    _schedule: List[Optional[ScheduleDay]]
    _day: int
    _params: Any
    _results: List[List[MatchResult]]

    def __init__(self, clubs: Dict[str, Club], params: Any, competition_id=None):
        self._clubs = clubs
        self._competition_id = competition_id or str(uuid4())
        self._day = 0
        self._params = params
        self._results = []
        self._schedule = []

    @property
    def competition_id(self):
        return self._competition_id

    @property
    def current_matches(self) -> Optional[ScheduleDay]:
        """List of current matches."""

        if self._day < len(self._schedule):
            return self._schedule[self._day]
        return []

    @property
    def day(self):
        """Current day of a competition."""

        return self._day

    @property
    def is_over(self) -> bool:
        """Checks if competition is over"""
        return False

    @property
    def match_importance(self) -> int:
        """Returns an importance factor of current matches."""
        return -1

    @property
    def match_params(self):
        return self._params.match_params

    @property
    def results_(self) -> Generator[List[MatchResult], None, None]:
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
        return []

    @property
    def title(self) -> str:
        """Title of the competition."""
        return ""

    def get_club_schedule(self, club_pk: str) -> List[ScheduledMatch]:
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

    def get_club_fame(self, club_pk: str) -> int:
        """Fame earned by club in the competition."""

    def apply_results(self, results: List[MatchResult]):
        """Applies externally processed match results to current matches."""

    def update(self) -> List[MatchResult]:
        """Updates the state of the competition."""

    def _make_match_processor(self) -> MatchEngine:
        return MatchEngine(self._params.match_params)

    def _make_schedule(self):
        pass

    def _validate_current_results(self, results: List[MatchResult]):
        current_matches = self.current_matches or []

        expected_ids = set(match.match_id for match in current_matches)
        actual_ids = set(result.match_id for result in results)
        assert expected_ids == actual_ids, (
            "Results do not match current scheduled matches."
        )

        matches_by_id = {
            match.match_id: match
            for match in current_matches
        }
        for result in results:
            match = matches_by_id[result.match_id]
            assert result.home_pk == match.home_pk, (
                "Result home club does not match scheduled match."
            )
            assert result.away_pk == match.away_pk, (
                "Result away club does not match scheduled match."
            )
