
"""
Created Apr 09, 2019

@author montreal91
"""

from random import randint

from typing import Any
from typing import Dict

from configuration.config_game import DdPlayerSkills
from configuration.config_game import DdGameplayConstants


_ENDURANCE_FACTOR = DdPlayerSkills.ENDURANCE_FACTOR
_PRECISION = 1


class DdPlayer:
    """A class that describes a tennis player."""

    _first_name: str
    _second_name: str
    _last_name: str

    _technique: int
    _endurance: int
    _exhaustion: int
    _experience: int

    _current_stamina: int
    _age: int

    def __init__(
        self,
        first_name,
        second_name,
        last_name,
        technique,
        endurance,
        age
    ):
        self._first_name = first_name
        self._second_name = second_name
        self._last_name = last_name
        self._technique = technique
        self._endurance = endurance
        self._age = age

        self._exhaustion = 0
        self._experience = 0
        self._current_stamina = self.max_stamina

    @property
    def actual_technique(self) -> float:
        stamina_factor = self._current_stamina / self.max_stamina / 10
        return round(self._technique * stamina_factor, _PRECISION)

    @property
    def current_stamina(self) -> int:
        return self._current_stamina

    @property
    def endurance(self) -> float:
        return round(self._endurance / 10, _PRECISION)

    @property
    def exhaustion(self) -> int:
        return self._exhaustion

    @property
    def json(self) -> Dict[str, Any]:
        return dict(
            first_name=self._first_name,
            second_name=self._second_name,
            last_name=self._last_name,
            technique=self.technique,
            endurance=self.endurance,
            current_stamina=self._current_stamina,
            actual_technique=self.actual_technique,
            level=self.level,
            age=self._age,
            exhaustion=self._exhaustion,
        )

    @property
    def level(self) -> int:
        """Current level of the player."""
        level = 0
        while _LevelExp(level) < self._experience:
            level += 1
        return level

    @property
    def max_stamina(self):
        return self._endurance * _ENDURANCE_FACTOR

    # 'exp' stands for experience
    @property
    def next_level_exp(self) -> int:
        return _LevelExp(self.level + 1)

    @property
    def technique(self):
        return round(self._technique / 10, _PRECISION)

    def AddExhaustion(self, value: int):
        """Adds Exhaustion."""

        self._exhaustion += value

    def AddExperience(self, experience: int):
        """Adds new experience.

        If necessary, levels up player.
        """
        old_level = self.level
        self._experience += experience
        new_level = self.level

        skill_delta = DdGameplayConstants.SKILL_GROWTH_PER_LEVEL.value
        while old_level < new_level:
            old_level += 1
            toss = randint(0, 1)
            if toss:
                self._technique += skill_delta
            else:
                self._endurance += skill_delta

    def AfterSeasonRest(self):
        self._exhaustion = 0
        self.RecoverStamina(self.max_stamina)

    def AgeUp(self):
        self._age += 1

    def RecoverStamina(self, recovered_stamina: int):
        self._current_stamina += recovered_stamina
        self._current_stamina = min(self._current_stamina, self.max_stamina)

    def RemoveStaminaLostInMatch(self, lost_stamina: int):
        self._current_stamina -= lost_stamina

    @staticmethod
    def CalculateNewExperience(sets_won: int, opponent: "DdPlayer") -> int:
        base = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value * sets_won
        factor = DdGameplayConstants.EXPERIENCE_LEVEL_FACTOR.value
        factor *= opponent.level
        factor /= 100   # 100%
        factor += 1
        return int(round(base * factor))


def ExhaustedRecovery(player: DdPlayer) -> int:
    """Player recovery function that involves exhaustion."""

    base = player.max_stamina
    res = base * (100 - player.exhaustion) / 100
    return int(round(res))


def PlayerModelComparator(player_model):
    """Function used to compare two players."""
    return player_model.actual_technique * 1.2 + player_model.endurance


def _LevelExp(n: int) -> int:
    """Total experience required to gain a level.

    Formula is based on the sum of arithmetic progression.
    """
    ec = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value
    return int((n * (n + 1) / 2) * ec)
