
"""
Created Apr 09, 2019

@author montreal91
"""

from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from configuration.config_game import sets_to_win
from simplified.player import DdPlayer
from stat_tools import LoadedToss


class DdSetStatuses(Enum):
    """Enumeration of possible set outcomes."""

    REGULAR = 1
    HOME_RETIRED = 2
    AWAY_RETIRED = 3


class DdSetResult(NamedTuple):
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
            return (0, 1)
        if self.set_status == DdSetStatuses.AWAY_RETIRED:
            return (1, 0)
        raise Exception("Bad set result (wrong status).")



class DdMatchResult:
    """A class with results of a single match."""

    _sets: List[DdSetResult]

    def __init__(self, sets_to_win: int = 2):
        self.home_pk = None
        self.away_pk = None
        self.home_player_snapshot = None
        self.away_player_snapshot = None
        self.surface = None
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
        return DdPlayer.CalculateNewExperience(
            self.away_sets, self.home_player_snapshot["level"]
        )

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
            f"{int(self.home_player_snapshot['speciality'] == self.surface)},"
            f"{self.home_sets},"
            f"{self.away_player_snapshot['actual_technique']},"
            f"{self.away_player_snapshot['current_stamina']},"
            f"{int(self.away_player_snapshot['speciality'] == self.surface)},"
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
        return DdPlayer.CalculateNewExperience(
            self.home_sets, self.away_player_snapshot["level"]
        )

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

    def AddSetResult(self, set_result: DdSetResult):
        """Adds set result to the match result."""

        self._sets.append(set_result)

    @property
    def _abnormal_set(self) -> Optional[DdSetResult]:
        abnormal_ends = (DdSetStatuses.HOME_RETIRED, DdSetStatuses.AWAY_RETIRED)
        for result in self._sets:
            if result.set_status in abnormal_ends:
                return result
        return None


class DdMatchParams(NamedTuple):
    """Passive class to store basic match parameters."""

    exhaustion_function: Callable[[int], int]
    probability_function: Callable[[float, float], float]
    reputation_function: Callable[[int], int]

    games_to_win: int = 6
    sets_to_win: int = 2
    speciality_bonus: float = 11.0


class DdMatchProcessor:
    """This class incapsulates inner logic of a tennis match."""

    _GAP: int = 2

    _match_surface: str
    _res: DdMatchResult
    _params: DdMatchParams
    _stamina_counter: Dict[str, int]

    def __init__(self, params: DdMatchParams):
        self._res = DdMatchResult()
        self._params = params
        self._stamina_counter = {
            "home": 0,
            "away": 0,
        }

    def ProcessMatch(
        self, home_player: DdPlayer, away_player: DdPlayer
    ) -> DdMatchResult:
        """Processes match and returns the results."""

        sets_played = 0
        self._res.surface = self._match_surface
        self._res.home_player_snapshot = home_player.json
        self._res.away_player_snapshot = away_player.json

        while not self._IsMatchOver():
            set_result = self._ProcessSet(
                home_player,
                away_player
            )
            sets_played += 1
            self._res.AddSetResult(set_result)

            home_player.AddReputation(
                self._reputation_function(set_result.home_games) * sets_played
            )
            away_player.AddReputation(
                self._reputation_function(set_result.away_games) * sets_played
            )

        home_player.AddExperience(self._res.home_exp)
        away_player.AddExperience(self._res.away_exp)

        home_player.RemoveStaminaLostInMatch(self._stamina_counter["home"])
        away_player.RemoveStaminaLostInMatch(self._stamina_counter["away"])

        exhaustion = self._exhaustion_function(sets_played)

        home_player.AddExhaustion(exhaustion)
        away_player.AddExhaustion(exhaustion)

        return deepcopy(self._res)

    def SetMatchSurface(self, surface: str):
        """Sets surface on which match will be held."""
        self._match_surface = surface

    def _CalculateActualSkill(self, player, actual_stamina=0):
        stamina_factor = actual_stamina / player.max_stamina
        good_speciality = player.speciality == self._match_surface
        bonus = self._params.speciality_bonus if good_speciality else 1.0
        return max(
            player.technique * stamina_factor + bonus,
            5
        )

    def _CalculateActualStamina(self, player, lost_stamina=0):
        return player.current_stamina - lost_stamina

    def _CalculateStaminaLostInGame(self):
        return 2

    def _IsSetOver(self, hgames: int, agames: int) -> bool:
        games_to_win = self._params.games_to_win
        cond1 = hgames >= games_to_win and hgames - agames >= self._GAP
        cond2 = agames >= games_to_win and agames - hgames >= self._GAP

        return cond1 or cond2

    def _IsMatchOver(self) -> bool:
        home_won = self._res.home_sets == self._params.sets_to_win
        away_won = self._res.away_sets == self._params.sets_to_win
        return home_won or away_won

    def _ProcessSet(self, home_player, away_player):
        home_games, away_games = 0, 0
        while not self._IsSetOver(home_games, away_games):
            home_stamina = self._CalculateActualStamina(
                home_player,
                lost_stamina=self._stamina_counter["home"]
            )
            away_stamina = self._CalculateActualStamina(
                away_player,
                lost_stamina=self._stamina_counter["away"]
            )
            home_actual_skill = self._CalculateActualSkill(
                home_player, home_stamina
            )
            away_actual_skill = self._CalculateActualSkill(
                away_player, away_stamina
            )

            if home_actual_skill == 0:
                return DdSetResult(
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.HOME_RETIRED
                )
            elif away_actual_skill == 0:
                return DdSetResult(
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.AWAY_RETIRED
                )

            toss = LoadedToss(self._probability_function(
                home_actual_skill, away_actual_skill
            ))

            if toss:
                home_games += 1
            else:
                away_games += 1

            self._stamina_counter["home"] += self._CalculateStaminaLostInGame()
            self._stamina_counter["away"] += self._CalculateStaminaLostInGame()

        return DdSetResult(
            home_games=home_games,
            away_games=away_games,
            set_status=DdSetStatuses.REGULAR,
        )

    @property
    def _exhaustion_function(self) -> Callable[[int], int]:
        return self._params.exhaustion_function

    @property
    def _probability_function(self) -> Callable[[float, float], float]:
        return self._params.probability_function

    @property
    def _reputation_function(self) -> Callable[[int], int]:
        return self._params.reputation_function


class DdScheduledMatchStruct:
    """Passive class for a scheduled match."""

    def __init__(self, home_pk, away_pk):
        self.home_pk = home_pk
        self.away_pk = away_pk
        self.is_played = False

    def __repr__(self):
        return f"<{self.home_pk} - {self.away_pk}>"

    @property
    def json(self):
        return dict(
            home_pk=self.home_pk,
            away_pk=self.away_pk,
            is_played=self.is_played,
        )


class DdStandingsRowStruct:
    """Passive class for a row in standings."""

    def __init__(self, club_pk: int):
        self.club_pk = club_pk
        self.matches_won = 0
        self.sets_won = 0
        self.games_won = 0

    @property
    def json(self) -> Dict[str, Any]:
        return dict(
            club_pk=self.club_pk,
            matches_won=self.matches_won,
            sets_won=self.sets_won,
            games_won=self.games_won,
        )


class DdExhaustionCalculator:
    """Callable class to calculate exhaustion gained in a match."""

    def __call__(self, sets):
        return self._k * sets

    def __init__(self, k):
        self._k = k


def NaiveProbabilityFunction(home_skill: float, away_skill: float) -> float:
    total_skill = home_skill + away_skill
    return home_skill / total_skill


def LinearProbabilityFunction(home_skill: float, away_skill: float) -> float:
    """Probability of winnig a game by home player.

    This function grows linearly on [-50, 50] interval depending on the
    difference between home and away skills. It takes values from
    0.05 to 0.95 at the ends of the interval and 0.5 in the middle.
    """
    delta = home_skill - away_skill

    if -50 <= delta <= 50:
        return round(0.009 * delta + 0.5, 6)
    elif delta < -50:
        return 0.05
    elif delta > 50:
        return 0.95
    return 0
