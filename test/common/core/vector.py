
"""
Created 2019.12.10

@author montreal91
"""

from pytest import raises

from common.core.vector import Vector


def TestArithmetic():
    """
    Smoke test for basic vector arithmetic.

    Tests addition, subtraction and multiplication by a scalar.
    """

    v1 = Vector((1, 2))
    v2 = Vector((2, 3))
    v3 = Vector((1, 2, 3))

    assert v1 + v1 == Vector((2, 4))
    assert v1 - v1 == Vector((0, 0))
    assert v1 + v2 == Vector((3, 5))

    with raises(ValueError):
        v1 + v3

    with raises(ValueError):
        v3 + v2

    diff = Vector((1, 0, 0, 0))
    v4 = Vector((0, 0, 1, 2))
    v4 += diff
    assert v4 == Vector((1, 0, 1, 2))

    v4 -= diff
    assert v4 == Vector((0, 0, 1, 2))

    assert v4 * 0.5 == Vector((0, 0, 0.5, 1.0))
    assert v3 * 2 == Vector((2, 4, 6))

    v2 *= 0
    assert v2 == Vector((0, 0))


def TestDefaultVector():
    """
    Smoke test for default vector.

    Vector shouldn't be used that way, but Just in case.
    """
    v00 = Vector()
    v01 = Vector()

    assert v00._vector == (0,)
    assert v00 == v01
    assert v00._vector is not v01._vector


def TestSmoke():
    """
    Smoke test for vector class.

    Creates four different vectors and checks simple logic of length
    function and comparing operators.
    """
    v1 = Vector((1, 2))
    v2 = Vector((1, 2, 3))
    v3 = Vector((1, 2, 4))
    v4 = Vector((1, 2, 4))
    assert len(v1) == 2
    assert len(v2) == 3
    assert len(v3) == 3
    assert len(v4) == 3

    assert not v1 == v2
    assert v1 != v2

    assert not v2 == v3
    assert v3 != v2

    assert v3 == v4
    assert not v4 != v3
