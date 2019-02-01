
from unittest import TestCase

from app.game.match_processor import LinearProbabilityFunction


class LinearProbabilityFunctionTestCase(TestCase):
    def test_full(self):
        home_skill = 70
        cases = (
            (home_skill + 60, 0.05),
            (home_skill + 50, 0.05),
            (home_skill, 0.5),
            (home_skill - 50, 0.95),
            (home_skill - 60, 0.95),
        )

        for case in cases:
            self.assertEqual(
                LinearProbabilityFunction(home_skill, case[0]), case[1]
            )
