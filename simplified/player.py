
"""
Created Apr 09, 2019

@author montreal91
"""

import json

from random import choice
from random import randint

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from configuration.config_game import DdPlayerSkills
from configuration.config_game import DdGameplayConstants
from simplified.serialization import DdField
from simplified.serialization import DdJsonable


_ENDURANCE_FACTOR = DdPlayerSkills.ENDURANCE_FACTOR
_PRECISION = 1


class DdCourtSurface:
    """
    All possible surfaces of courts.

    Constant.
    """
    CLAY = "clay"
    GRASS = "grass"
    HARD = "hard"


class DdPlayerStats(DdJsonable):
    """A passive data structure to store player stats."""

    sets_played: int
    sets_won: int
    matches_played: int
    matches_won: int

    _FIELD_MAP = (
        DdField("sets_played", "sets_played"),
        DdField("sets_won", "sets_won"),
        DdField("matches_played", "matches_played"),
        DdField("matches_won", "matches_won"),
    )

    def __init__(self):
        self.sets_played = 0
        self.sets_won = 0
        self.matches_played = 0
        self.matches_won = 0


class DdPlayer(DdJsonable):
    """A class that describes a tennis player."""

    _FIELD_MAP = (
        DdField("_first_name", "first_name"),
        DdField("_second_name", "second_name"),
        DdField("_last_name", "last_name"),
        DdField("_technique", "technique"),
        DdField("_endurance", "endurance"),
        DdField("_exhaustion", "exhaustion"),
        DdField("_experience", "experience"),
        DdField("_speciality", "speciality"),
        DdField("_current_stamina", "current_stamina"),
        DdField("_age", "age"),
        DdField("_reputation", "reputation"),
    )

    _first_name: str
    _second_name: str
    _last_name: str

    _technique: int
    _endurance: int
    _exhaustion: int
    _experience: int
    _speciality: str

    _current_stamina: int
    _age: int

    _reputation: int
    _stats: DdPlayerStats

    def __init__(
        self,
        first_name: str = "Joan",
        second_name: str = "Katelyn",
        last_name: str = "Rowling",
        technique: int = 1,
        endurance: int = 1,
        age: int = 30,
        speciality: str = DdCourtSurface.HARD,
    ):
        self._first_name = first_name
        self._second_name = second_name
        self._last_name = last_name
        self._technique = technique
        self._endurance = endurance
        self._age = age
        self._speciality = speciality

        self._exhaustion = 0
        self._experience = 0
        self._current_stamina = self.max_stamina
        self._reputation = 0
        self._stats = DdPlayerStats()

    @property
    def age(self):
        return self._age

    @property
    def actual_technique(self) -> float:
        stamina_factor = self._current_stamina / self.max_stamina
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
    def experience(self) -> int:
        """Player's current experience."""

        return self._experience

    @property
    def full_name(self) -> str:
        """Full name of the player."""

        return f"{self._first_name} {self._second_name} {self._last_name}"

    @property
    def initials(self) -> str:
        """The name of the player in form of 'J. K. Rowling'."""

        return "{0:s}. {1:s}. {2:s}".format(
            self._first_name[0],
            self._second_name[0],
            self._last_name
        )

    @property
    def json(self) -> Dict[str, Any]:
        return dict(
            first_name=self._first_name,
            second_name=self._second_name,
            last_name=self._last_name,
            technique=self.technique,
            endurance=self.endurance,
            current_stamina=self._current_stamina,
            max_stamina=self.max_stamina,
            actual_technique=self.actual_technique,
            level=self.level,
            age=self._age,
            exhaustion=self._exhaustion,
            reputation=self._reputation,
            speciality=self._speciality,
        )

    @property
    def level(self) -> int:
        """Current level of the player."""
        level = 0
        while not self._experience < _LevelExp(level + 1):
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
    def reputation(self) -> int:
        """Shows player reputation level among audience."""

        return self._reputation

    @property
    def speciality(self) -> str:
        return self._speciality

    @property
    def stats(self) -> DdPlayerStats:
        return self._stats

    @property
    def technique(self):
        return self._technique

    def AddExhaustion(self, value: int):
        """Adds Exhaustion."""

        self._exhaustion += value

    def AddExperience(self, experience: int):
        """
        Adds new experience.

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

    def AddReputation(self, rep: int):
        """Adds new reputation."""
        self._reputation += rep

    def AfterSeasonRest(self):
        self._exhaustion = 0
        self.RecoverStamina(self.max_stamina)

    def AgeUp(self):
        self._age += 1

    def DropStats(self):
        self._stats = DdPlayerStats()

    def RecoverStamina(self, recovered_stamina: int):
        self._current_stamina += recovered_stamina
        self._current_stamina = min(self._current_stamina, self.max_stamina)

    def RemoveStaminaLostInMatch(self, lost_stamina: int):
        self._current_stamina -= lost_stamina

    @staticmethod
    def CalculateNewExperience(sets_won: int, opponent_level: int) -> int:
        base = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value * sets_won
        factor = DdGameplayConstants.EXPERIENCE_LEVEL_FACTOR.value
        factor *= opponent_level
        factor /= 100   # 100%
        factor += 1
        return int(round(base * factor))


class DdPlayerFactory:
    _first_names: List[str]
    _last_names: List[str]

    def __init__(self):
        self._first_names, self._last_names = _LoadNames()

    def CreatePlayer(self, level: int, age: int, speciality: str) -> DdPlayer:
        """
        Creates a player object of given age and level.
        """
        skill_base = DdGameplayConstants.SKILL_BASE.value

        player = DdPlayer(
            age=age,
            first_name=choice(self._first_names),
            second_name=choice(self._first_names),
            last_name=choice(self._last_names),
            technique=skill_base,
            endurance=skill_base,
            speciality=speciality,
        )

        player.AddExperience(_LevelExp(level))
        player.AfterSeasonRest()

        return player


class DdPlayerReputationCalculator:
    """
    Simple callable class to calculate player's reputation gained per set.

    Basically, it constructs a linear function that depends on games won and
    """

    def __call__(self, games: int) -> int:
        return self._k * (games - self._games_to_win // 2)

    def __init__(self, games_to_win: int, k: int):
        self._games_to_win = games_to_win
        self._k = k


def ExhaustedRecovery(player: DdPlayer) -> int:
    """Player recovery function that involves exhaustion.

    Naive exhaustion.
    """

    base = player.max_stamina
    res = base * (100 - player.exhaustion) / 100
    return int(round(res))


class DdExhaustedLinearRecovery:
    """
    Callable class of recovery functions that involve exhaustion.

    Linear exhaustion, i.e. dependency of days to fully recover from exhaustion
    is linear.
    """
    def __call__(self, player: DdPlayer) -> int:
        days_to_recover = player.exhaustion // self._exhaustion_factor + 1
        return int(round(player.max_stamina / days_to_recover))

    def __init__(self, exhaustion_factor):
        self._exhaustion_factor = exhaustion_factor


def PlayerModelComparator(player_model):
    """Function used to compare two players."""
    return player_model.actual_technique * 1.2 + player_model.endurance


def _LevelExp(n: int) -> int:
    """Total experience required to gain a level.

    Formula is based on the sum of arithmetic progression.
    """
    ec = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value
    return int((n * (n + 1) / 2) * ec)


def _LoadNames() -> Tuple[List[str], List[str]]:
    """Utility function that loads names from the file on the disk."""
    with open("configuration/names.json") as datafile:
        all_names = json.load(datafile)
    return all_names["names"], all_names["surnames"]
