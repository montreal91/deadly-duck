
"""
N-dimentional vector. A VALUE OBJECT that contains only numerical values.

Created 2019.12.09

@author montreal91
"""

from typing import Tuple

from unittest import TestCase


class Vector:
    """N-dimentional vector. Behaves almost like a mathematical vector."""

    _vector: Tuple[float, ...]

    def __init__(self, values: Tuple[float, ...]):
        self._vector = values

    def __len__(self):
        return len(self._vector)

    def __add__(self, other: "Vector") -> "Vector":
        if len(self) != len(other):
            raise ValueError(
                "It's impossible to add vector of a different length."
            )
        return Vector(
            tuple(a + b for a, b in zip(self._vector, other._vector))
        )

    def __sub__(self, other: "Vector") -> "Vector":
        if len(self) != len(other):
            raise ValueError(
                "It's impossible to subtract vector of a different length."
            )
        return Vector(
            tuple(a - b for a, b in zip(self._vector, other._vector))
        )

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(tuple(a * scalar for a in self._vector))

    def __eq__(self, other) -> bool:
        return self._vector == other._vector

    def __ne__(self, other) -> bool:
        return not self == other



class VectorTestCase(TestCase):
    def test_smoke(self):
        """
        Smoke test for vector class.

        Creates four different vectors and checks simple logic of length
        function and comparing operators.
        """
        v1 = Vector((1, 2))
        v2 = Vector((1, 2, 3))
        v3 = Vector((1, 2, 4))
        v4 = Vector((1, 2, 4))
        self.assertEqual(len(v1), 2)
        self.assertEqual(len(v2), 3)
        self.assertEqual(len(v3), 3)
        self.assertEqual(len(v4), 3)

        self.assertFalse(v1 == v2)
        self.assertTrue(v1 != v2)

        self.assertFalse(v2 == v3)
        self.assertTrue(v3 != v2)

        self.assertTrue(v3 == v4)
        self.assertFalse(v4 != v3)


    def test_arithmetic(self):
        """
        Smoke test for basic vector arithmetic.

        Tests addition, subtraction and multiplication by a scalar.
        """

        v1 = Vector((1, 2))
        v2 = Vector((2, 3))
        v3 = Vector((1, 2, 3))

        self.assertEqual(v1 + v1, Vector((2, 4)))
        self.assertEqual(v1 - v1, Vector((0, 0)))
        self.assertEqual(v1 + v2, Vector((3, 5)))

        with self.assertRaises(ValueError):
            v1 + v3

        with self.assertRaises(ValueError):
            v3 + v2

        diff = Vector((1, 0, 0, 0))
        v4 = Vector((0, 0, 1, 2))
        v4 += diff
        self.assertEqual(v4, Vector((1, 0, 1, 2)))

        v4 -= diff
        self.assertEqual(v4, Vector((0, 0, 1, 2)))

        self.assertEqual(v4 * 0.5, Vector((0, 0, 0.5, 1.0)))
        self.assertEqual(v3 * 2, Vector((2, 4, 6)))

        v2 *= 0
        self.assertEqual(v2, Vector((0, 0)))
