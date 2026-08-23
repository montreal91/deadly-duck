"""
Created Aug 22, 2026

@author montreal91
"""
from typing import List
from typing import Optional

from configuration.config_game import GameplayConstants
from core.set_result import SetResult
from core.set_result import DdSetStatuses


class MatchResult:
    """A class with results of a single match."""

    _sets: List[SetResult]

    def __init__(self, sets_to_win: int = 2):
        self.match_id = None
        self.home_pk = None
        self.away_pk = None
        self.home_player_snapshot = None
        self.away_player_snapshot = None
        self.attendance = 0
        self.income = 0
        self._sets_to_win = sets_to_win
        self._sets = []

    def __len__(self) -> int:
        return len(self._sets)

    def __repr__(self):
        return (
            f"<# ({id(self)}) {self.home_pk} vs {self.away_pk} "
            f"{self.full_score}"
            " >"
        )

    @property
    def away_exp(self) -> int:
        """Experience gained by away player."""

        if self.home_player_snapshot is None:
            return 0
        return _calculate_new_experience(self.away_games)

    @property
    def away_games(self) -> int:
        """Games won by away player."""

        return sum(set_result.away_games for set_result in self._sets)

    @property
    def away_sets(self):
        """Sets won by away player."""

        bad_set = self._abnormal_set
        if bad_set is None:
            return sum(set_result.score[1] for set_result in self._sets)

        if bad_set.score[1] == 1:
            return self._sets_to_win
        return 0

    @property
    def csv(self) -> str:
        """Comma separated values of the match for statistic purposes."""

        return (
            f"{self.home_player_snapshot['actual_technique']},"
            f"{self.home_player_snapshot['current_stamina']},"
            f"{self.home_sets},"
            f"{self.away_player_snapshot['actual_technique']},"
            f"{self.away_player_snapshot['current_stamina']},"
            f"{self.away_sets}"
        )

    @property
    def full_score(self):
        """Full score of the match."""

        return " ".join(str(res) for res in self._sets)

    @property
    def home_exp(self):
        """Experience gained by home player."""

        if self.away_player_snapshot is None:
            return 0
        return _calculate_new_experience(self.home_games)

    @property
    def home_games(self) -> int:
        """Games won by home player."""

        return sum(set_result.home_games for set_result in self._sets)

    @property
    def home_sets(self):
        """Sets won by home player."""

        bad_set = self._abnormal_set
        if bad_set is None:
            return sum(set_result.score[0] for set_result in self._sets)

        if bad_set.score[0] == 1:
            return self._sets_to_win
        return 0

    def AddSetResult(self, set_result: SetResult):
        """Adds set result to the match result."""

        self._sets.append(set_result)

    @property
    def _abnormal_set(self) -> Optional[SetResult]:
        abnormal_ends = (DdSetStatuses.HOME_RETIRED, DdSetStatuses.AWAY_RETIRED)
        for result in self._sets:
            if result.set_status in abnormal_ends:
                return result
        return None


def _calculate_new_experience(games_won: int) -> int:
    return games_won * GameplayConstants.EXPERIENCE_COEFFICIENT.value
