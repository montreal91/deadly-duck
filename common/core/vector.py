
"""
N-dimentional vector. A VALUE OBJECT that contains only numerical values.

Created 2019.12.09

@author montreal91
"""

from typing import Tuple

from attr import Factory
from attr import s


def _zero_vector():
    return tuple([0])


@s(auto_attribs=True)
class Vector:
    """N-dimentional vector. Behaves almost like a mathematical vector."""

    _vector: Tuple[float, ...] = Factory(_zero_vector)

    def __add__(self, other: "Vector") -> "Vector":
        if len(self) != len(other):
            raise ValueError(
                "It's impossible to add vector of a different length."
            )
        return Vector(
            tuple(a + b for a, b in zip(self._vector, other._vector))
        )

    def __eq__(self, other) -> bool:
        return self._vector == other._vector

    def __init__(self, values: Tuple[float, ...]):
        self._vector = values

    def __len__(self):
        return len(self._vector)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(tuple(a * scalar for a in self._vector))

    def __ne__(self, other) -> bool:
        return not self == other

    def __sub__(self, other: "Vector") -> "Vector":
        if len(self) != len(other):
            raise ValueError(
                "It's impossible to subtract vector of a different length."
            )
        return Vector(
            tuple(a - b for a, b in zip(self._vector, other._vector))
        )
