
"""
Created Apr 09, 2019

@author montreal91
"""

import json
import uuid
from enum import Enum
from random import choice
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from configuration.config_game import GameplayConstants
from configuration.config_game import DdPlayerSkills
from core.serialization import DdField
from core.serialization import Jsonable

_ENDURANCE_FACTOR = DdPlayerSkills.ENDURANCE_FACTOR
_PRECISION = 1


# TODO: Get rid of Jsonable stuff
class PlayerStats(Jsonable):
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


class SkillSet(Enum):
    TECHNIQUE = "technique"
    ENDURANCE = "endurance"


class Player(Jsonable):
    """A class that describes a tennis player."""

    _FIELD_MAP = (
        DdField("_player_id", "player_id"),
        DdField("_first_name", "first_name"),
        DdField("_second_name", "second_name"),
        DdField("_last_name", "last_name"),
        DdField("_technique", "technique"),
        DdField("_endurance", "endurance"),
        DdField("_exhaustion", "exhaustion"),
        DdField("_experience", "experience"),
        DdField("_skill_points", "skill_points"),
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
    _skill_points: int

    _current_stamina: int
    _age: int

    _reputation: int
    _stats: PlayerStats

    def __init__(
        self,
        first_name: str = "Joan",
        second_name: str = "Katelyn",
        last_name: str = "Rowling",
        technique: int = 1,
        endurance: int = 1,
        age: int = 30,
    ):
        self._player_id = str(uuid.uuid4())
        self._first_name = first_name
        self._second_name = second_name
        self._last_name = last_name
        self._technique = technique
        self._endurance = endurance
        self._age = age

        self._exhaustion = 0
        self._experience = 0
        self._skill_points = 0
        self._current_stamina = self.max_stamina
        self._reputation = 0
        self._stats = PlayerStats()

    def __from_json__(self, data: Dict[str, Any]):
        data.setdefault("skill_points", 0)
        super().__from_json__(data)

    @property
    def age(self):
        return self._age

    @property
    def actual_technique(self) -> float:
        return self.calculate_actual_technique(self._current_stamina)

    def calculate_actual_technique(self, actual_stamina: float) -> float:
        stamina_factor = actual_stamina / self.max_stamina
        min_technique = self._technique * 0.1
        return round(
            max(self._technique * stamina_factor, min_technique),
            _PRECISION,
        )

    @property
    def current_stamina(self) -> int:
        return self._current_stamina

    @property
    def endurance(self) -> int:
        return self._endurance

    @property
    def exhaustion(self) -> int:
        return self._exhaustion

    @property
    def experience(self) -> int:
        """Player's current experience."""

        return self._experience

    @property
    def skill_points(self) -> int:
        return self._skill_points

    @property
    def first_name(self):
        return self._first_name

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
            player_id=self.player_id,
            first_name=self._first_name,
            second_name=self._second_name,
            last_name=self._last_name,
            technique=self.technique,
            endurance=self.endurance,
            current_stamina=self._current_stamina,
            max_stamina=self.max_stamina,
            actual_technique=self.actual_technique,
            level=self.level,
            skill_points=self._skill_points,
            age=self._age,
            exhaustion=self._exhaustion,
            reputation=self._reputation,
        )

    @property
    def second_name(self):
        return self._second_name

    @property
    def last_name(self):
        return self._last_name

    @property
    def player_id(self) -> str:
        return self._player_id

    @property
    def level(self) -> int:
        """Current level of the player."""
        level = 0
        while not self._experience < level_exp(level + 1):
            level += 1
        return level

    @property
    def max_stamina(self):
        return self._endurance * _ENDURANCE_FACTOR

    # 'exp' stands for experience
    @property
    def next_level_exp(self) -> int:
        return level_exp(self.level + 1)

    @property
    def reputation(self) -> int:
        """Shows player reputation level among audience."""

        return self._reputation

    @property
    def stats(self) -> PlayerStats:
        return self._stats

    @property
    def technique(self) -> int:
        return self._technique

    def AddExhaustion(self, value: int):
        """Adds Exhaustion."""

        self._exhaustion += value

    def improve_skill(self, skill_points: int, skill: SkillSet):
        if skill_points > self._skill_points or skill_points < 0:
            return # No skill improvement beyond limits or negative improvement

        skill_growth_coefficient = GameplayConstants.SKILL_GROWTH_PER_POINT.value

        if skill == SkillSet.TECHNIQUE:
            self._technique += skill_points * skill_growth_coefficient
        elif skill == SkillSet.ENDURANCE:
            self._endurance += skill_points * skill_growth_coefficient
        else:
            raise ValueError("Unknown skill")

        self._skill_points -= skill_points

    def add_experience(self, experience: int):
        """
        Adds new experience.

        If necessary, levels up player.
        """
        old_level = self.level
        self._experience += experience
        new_level = self.level

        while old_level < new_level:
            old_level += 1
            self._skill_points += GameplayConstants.SKILL_POINTS_PER_LEVEL.value

    def AddReputation(self, rep: int):
        """Adds new reputation."""
        self._reputation += rep

    def AfterSeasonRest(self):
        self._exhaustion = 0
        self.RecoverStamina(self.max_stamina)

    def AgeUp(self):
        self._age += 1

    def DropStats(self):
        self._stats = PlayerStats()

    def RecoverStamina(self, recovered_stamina: int):
        self._current_stamina += recovered_stamina
        self._current_stamina = max(self._current_stamina, 0)
        self._current_stamina = min(self._current_stamina, self.max_stamina)

    def RemoveStaminaLostInMatch(self, lost_stamina: int):
        self._current_stamina -= lost_stamina
        self._current_stamina = max(self._current_stamina, 0)


class PlayerFactory:
    _first_names: List[str]
    _last_names: List[str]

    def __init__(self):
        self._first_names, self._last_names = _load_names()

    def create_player(self, level: int, age: int) -> Player:
        """
        Creates a player object of given age and level.
        """
        skill_base = GameplayConstants.SKILL_BASE.value

        player = Player(
            age=age,
            first_name=choice(self._first_names),
            second_name=choice(self._first_names),
            last_name=choice(self._last_names),
            technique=skill_base,
            endurance=skill_base,
        )

        player.add_experience(level_exp(level))
        player.AfterSeasonRest()

        return player


class PlayerReputationCalculator:
    """
    Simple callable class to calculate player's reputation gained per set.

    Basically, it constructs a linear function that depends on games won and
    """

    def __call__(self, games: int) -> int:
        return self._k * (games - self._games_to_win // 2)

    def __init__(self, games_to_win: int, k: int):
        self._games_to_win = games_to_win
        self._k = k


def exhausted_recovery(player: Player) -> int:
    """Player recovery function that involves exhaustion.

    Naive exhaustion.
    """

    base = player.max_stamina
    res = base * (100 - player.exhaustion) / 100
    return int(round(res))


class ExhaustedLinearRecovery:
    """
    Callable class of recovery functions that involve exhaustion.

    Linear exhaustion, i.e. dependency of days to fully recover from exhaustion
    is linear.
    """
    def __call__(self, player: Player) -> int:
        days_to_recover = player.exhaustion // self._exhaustion_factor + 1
        return int(round(player.max_stamina / days_to_recover))

    def __init__(self, exhaustion_factor):
        self._exhaustion_factor = exhaustion_factor


def player_model_comparator(player_model):
    """Function used to compare two players."""
    return player_model.actual_technique * 1.2 + player_model.endurance


def level_exp(n: int) -> int:
    """Total experience required to gain a level.

    Formula is based on the sum of arithmetic progression.
    """
    ec = GameplayConstants.LEVEL_EXPERIENCE_COEFFICIENT.value
    return int((n * (n + 1) / 2) * ec)


def _load_names() -> Tuple[List[str], List[str]]:
    """Utility function that loads names from the file on the disk."""
    with open("data/names.json") as datafile:
        all_names = json.load(datafile)
    return all_names["names"], all_names["surnames"]
