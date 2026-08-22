"""
Created Aug 22, 2026

@author montreal91
"""
from enum import Enum
from typing import NamedTuple
from typing import Tuple


class DdSetStatuses(Enum):
    """Enumeration of possible set outcomes."""

    REGULAR = 1
    HOME_RETIRED = 2
    AWAY_RETIRED = 3


class SetResult(NamedTuple):
    """A class with results of a single set."""

    away_games: int
    home_games: int
    set_status: DdSetStatuses

    def __str__(self) -> str:
        """String representation of the set result."""

        if self.set_status == DdSetStatuses.REGULAR:
            return f"{self.home_games}:{self.away_games}"
        if self.set_status == DdSetStatuses.HOME_RETIRED:
            return f"Ret:{self.away_games}"
        if self.set_status == DdSetStatuses.AWAY_RETIRED:
            return f"{self.home_games}:Ret"
        raise Exception("Bad set result (wrong status).")

    @property
    def score(self) -> Tuple[int, int]:
        """
        Score of the set.

        If the set is won by home player, returns (1, 0).
        If the set is won by away player, returns (0, 1).
        Any other way is not possible and an exception is raised.
        """

        if self.set_status == DdSetStatuses.REGULAR:
            return (1, 0) if self.home_games > self.away_games else (0, 1)
        if self.set_status == DdSetStatuses.HOME_RETIRED:
            return 0, 1
        if self.set_status == DdSetStatuses.AWAY_RETIRED:
            return 1, 0
        raise Exception("Bad set result (wrong status).")
