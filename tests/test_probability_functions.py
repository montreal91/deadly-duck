
"""This file contains various tests for calculations of winning chances.

Created on Feb 2, 2019

@author: montreal91
"""

from unittest import TestCase

from app.game.match_processor import LinearProbabilityFunction


class ProbabilityFunctionsTestCase(TestCase):
    """Test case for probability functions."""

    def test_linear_probability_function(self):
        """Test for linear probability function."""

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
