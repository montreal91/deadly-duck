
"""
Created Apr 26, 2019

@author montreal91
"""

from typing import Callable
from typing import NamedTuple

from simplified.player import DdPlayer


class DdGameParams(NamedTuple):
    """Passive class to store game parameters"""

    exdiv_matches: int
    exhaustion_function: Callable[[int], int]
    exhaustion_per_set: int
    indiv_matches: int

    # This value should be a power of two
    playoff_clubs: int

    probability_function: Callable[[float, float], float]
    recovery_day: int
    recovery_function: Callable[[DdPlayer], int]
