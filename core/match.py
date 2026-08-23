
"""
Created Apr 09, 2019

@author montreal91
"""


class ExhaustionCalculator:
    """Callable class to calculate exhaustion gained in a match."""

    _coefficient: int

    def __call__(self, sets: int) -> int:
        return self._coefficient * sets

    def __init__(self, coefficient: int):
        self._coefficient = coefficient


def naive_probability_function(home_skill: float, away_skill: float) -> float:
    total_skill = home_skill + away_skill
    return home_skill / total_skill


class DdLinearProbabilityCalculator:
    """
    Probability of winning a game by home player.

    This function grows linearly on [-50, 50] interval depending on the
    difference between home and away skills. It takes values from
    0.05 to 0.95 at the ends of the interval and 0.5 in the middle.
    """
    def __call__(self, home_skill: float, away_skill: float) -> float:
        delta = home_skill - away_skill

        val = round(self._koefficient * delta + 0.5, 6)
        return min(max(val, 0.005), 0.995)

    def __init__(self, koefficient: float):
        self._koefficient = koefficient
