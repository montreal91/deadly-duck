
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

from configuration.config_game import sets_to_win
from simplified.player import DdPlayer
from stat_tools import LoadedToss


DdSetResult = namedtuple(
    "DdSetResult", [
        "home_games",
        "away_games",
        "set_status",
    ],
    rename=True
)


class DdSetStatuses(Enum):
    """Enumeration of possible set outcomes."""

    REGULAR = 1
    HOME_RETIRED = 2
    AWAY_RETIRED = 3


class DdMatchResult:
    """A class with results of a single match."""

    def __init__(self):
        self.home_pk = None
        self.away_pk = None
        self.home_games = 0
        self.away_games = 0
        self.home_exp = 0
        self.away_exp = 0
        self.home_stamina_lost = 0
        self.away_stamina_lost = 0

        self._away_sets = 0
        self._home_sets = 0
        self._full_score = ""


    def __repr__(self):
        string = "<{score}, stamina: {home_stamina:2d}:{away_stamina:2d}>"
        return string.format(
            score=self._full_score,
            home_stamina=self.home_stamina_lost,
            away_stamina=self.away_stamina_lost,
        )

    @property
    def away_sets(self):
        return self._away_sets

    @away_sets.setter
    def away_sets(self, value):
        """
        This setter should be used only to deal exceptional match result.
        """
        assert value >= 0, "Number of sets should be greater than 0."
        assert value <= sets_to_win, (
            "Number of sets should be lesser than %r." % sets_to_win
        )
        self._away_sets = int(value)

    @property
    def full_score(self):
        return self._full_score

    @property
    def home_sets(self):
        return self._home_sets

    @home_sets.setter
    def home_sets(self, value):
        """
        This setter should be used only to deal exceptional match result.
        """
        assert value >= 0, "Number of sets should be greater than 0."
        assert value <= sets_to_win, (
            "Number of sets should be lesser than %r." % sets_to_win
        )
        self._home_sets = int(value)

    def AppendSetToFullScore(self, set_result):
        s = "{0:d}:{1:d}".format(set_result.home_games, set_result.away_games)
        if set_result.set_status == DdSetStatuses.HOME_RETIRED:
            s += " Rt:W"
        elif set_result.set_status == DdSetStatuses.AWAY_RETIRED:
            s += " W:Rt"

        if self._full_score:
            self._full_score += " "
        self._full_score += s


class DdMatchProcessor:
    """This class incapsulates inner logic of a tennis match."""

    _exhaustion_function: Callable[[int], int]
    _probability_function: Callable[[float, float], float]
    _res: DdMatchResult

    def __init__(
        self,
        exhaustion_function: Callable[[int], int],
        probability_function: Callable[[float, float], float]
    ):
        self._exhaustion_function = exhaustion_function
        self._probability_function = probability_function
        self._res = DdMatchResult()

    def ProcessMatch(
        self, home_player, away_player, sets_to_win=2
    ) -> DdMatchResult:
        """Processes match and returns the results."""
        while not self._IsMatchOver(
            self._res.home_sets, self._res.away_sets, sets_to_win
        ):
            set_result = self._ProcessSet(
                home_player,
                away_player
            )
            self._res.home_games += set_result.home_games
            self._res.away_games += set_result.away_games
            self._res.AppendSetToFullScore(
                set_result
            )
            if set_result.home_games > set_result.away_games:
                self._res.home_sets += 1
            else:
                self._res.away_sets += 1

            if set_result.set_status == DdSetStatuses.HOME_RETIRED:
                self._res.away_sets = sets_to_win
                self._res.home_sets = 0
                break
            elif set_result.set_status == DdSetStatuses.AWAY_RETIRED:
                self._res.home_sets = sets_to_win
                self._res.away_sets = 0
                break

        self._res.home_exp = DdPlayer.CalculateNewExperience(
            self._res.home_sets, away_player
        )
        self._res.away_exp = DdPlayer.CalculateNewExperience(
            self._res.away_sets, home_player
        )

        home_player.AddExperience(self._res.home_exp)
        away_player.AddExperience(self._res.away_exp)

        home_player.RemoveStaminaLostInMatch(self._res.home_stamina_lost)
        away_player.RemoveStaminaLostInMatch(self._res.away_stamina_lost)

        exhaustion = self._exhaustion_function(
            self._res.home_sets + self._res.away_sets
        )

        home_player.AddExhaustion(exhaustion)
        away_player.AddExhaustion(exhaustion)

        return deepcopy(self._res)

    def _CalculateActualSkill(self, player, actual_stamina=0):
        stamina_factor = actual_stamina / player.max_stamina
        return max(
            player.technique * stamina_factor,
            5
        )

    def _CalculateActualStamina(self, player, lost_stamina=0):
        return player.current_stamina - lost_stamina

    def _CalculateStaminaLostInGame(self):
        return 2

    def _IsSetOver(self, hgames, agames):
        c1 = hgames >= 6 and hgames - agames >= 2
        c2 = agames >= 6 and agames - hgames >= 2

        return c1 or c2

    def _IsMatchOver(self, hsets, asets, sets_to_win):
        return hsets == sets_to_win or asets == sets_to_win

    def _ProcessSet(self, home_player, away_player):
        home_games, away_games = 0, 0
        while not self._IsSetOver(home_games, away_games):
            home_stamina = self._CalculateActualStamina(
                home_player,
                lost_stamina=self._res.home_stamina_lost
            )
            away_stamina = self._CalculateActualStamina(
                away_player,
                lost_stamina=self._res.away_stamina_lost
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

            self._res.home_stamina_lost += self._CalculateStaminaLostInGame()
            self._res.away_stamina_lost += self._CalculateStaminaLostInGame()

        return DdSetResult(
            home_games=home_games,
            away_games=away_games,
            set_status=DdSetStatuses.REGULAR,
        )


class DdScheduledMatchStruct:
    """Passive class for a scheduled match."""

    def __init__(self, home_pk, away_pk):
        self.home_pk = home_pk
        self.away_pk = away_pk
        self.is_played = False

    @property
    def json(self):
        return dict(
            home_pk=self.home_pk,
            away_pk=self.away_pk,
            is_played=self.is_played,
        )



class DdStandingsRowStruct:
    """Passive class for a row in standings."""

    def __init__(self, club_name: str):
        self.club_name = club_name
        self.matches_won = 0
        self.sets_won = 0
        self.games_won = 0

    @property
    def json(self) -> Dict[str, Any]:
        return dict(
            club_name=self.club_name,
            matches_won=self.matches_won,
            sets_won=self.sets_won,
            games_won=self.games_won,
        )

def CalculateConstExhaustion(sets: int) -> int:
    return sets

def CalculateLinearExhaustion(sets: int) -> int:
    return sum(range(sets + 1))


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
        return round(0.009 * delta + 0.5, 2)
    elif delta < -50:
        return 0.05
    elif delta > 0.95:
        return 0.95
    return 0
