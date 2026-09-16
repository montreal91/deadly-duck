
"""
Created May 20, 2019

@author montreal91
"""
import pickle
from copy import copy
from enum import Enum
from itertools import chain
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from uuid import uuid4

from core.match_result import MatchResult
from core.scheduled_match import ScheduledMatch


class CompetitionType(Enum):
    CHAMPIONSHIP = "championship"
    PLAY_OFFS = "play_offs"


class AbstractCompetition:
    """Abstract competition class."""

    _club_ids: List[str]
    _competition_id: str
    _schedule: Dict[int, List[ScheduledMatch]]
    _day: int
    _params: Any
    _results: Dict[int, List[MatchResult]]
    _is_over: bool

    @staticmethod
    def reconstruct(blob, day: int) -> "AbstractCompetition":
        res = pickle.loads(blob)
        res._day = day
        return res

    def __init__(
            self,
            club_ids: List[str],
            params: Any,
            competition_id=None,
    ):
        self._club_ids = list(club_ids)
        self._competition_id = competition_id or str(uuid4())
        self._day = 0
        self._params = params
        self._results = {}
        self._schedule = {}
        self._is_over = False

    @property
    def competition_id(self):
        return self._competition_id

    @property
    def current_matches(self) -> List[ScheduledMatch]:
        """List of current matches."""

        return self._schedule.get(self._day, [])

    @property
    def day(self):
        """Current day of a competition."""

        return self._day

    @property
    def is_over(self) -> bool:
        """Checks if competition is over"""
        return self._is_over

    @property
    def match_importance(self) -> int:
        """Returns an importance factor of current matches."""
        return -1

    @property
    def match_params(self):
        return self._params.match_params

    @property
    def results_for_tests(self) -> Generator[MatchResult, None, None]:
        """
        List of match results.

        Actually, this method is present here for testing purposes and should
        not be used for production.
        """
        if isinstance(self._results, dict):
            result_days = self._results.values()
        else:
            result_days = self._results

        for match in chain(*result_days):
            yield copy(match)

    def contains_club(self, club_pk: str) -> bool:
        return club_pk in self._club_ids

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
        for day in _schedule_days(self._schedule, self._day):
            if day is None:
                continue
            for match in day:
                if match.is_played:
                    continue
                if club_pk in (match.home_pk, match.away_pk):
                    schedule.append(match)
        return schedule

    def get_club_schedule_days(self, club_pk: str) -> List[Optional[ScheduledMatch]]:
        """List of upcoming competition days with optional club match."""

        schedule = []
        for day in _schedule_days(self._schedule, self._day):
            if day is None:
                schedule.append(None)
                continue

            club_match = None
            for match in day:
                if match.is_played:
                    continue
                if club_pk in (match.home_pk, match.away_pk):
                    club_match = match
                    break

            schedule.append(club_match)

        while schedule and schedule[-1] is None:
            schedule.pop()

        return schedule

    def get_club_fame(self, club_pk: str) -> int:
        """Fame earned by club in the competition."""

    def apply_results(self, results: List[MatchResult]):
        """Applies externally processed match results to current matches."""

    def make_schedule(self):
        pass

    def get_full_schedule(self) -> List[ScheduledMatch]:
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


def _schedule_days(schedule, start_day):
    if isinstance(schedule, list):
        return schedule[start_day:]

    return [
        schedule[day_number]
        for day_number in sorted(schedule)
        if day_number >= start_day
    ]
