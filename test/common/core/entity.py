
"""
Created 2019.12.10

@author montreal91
"""

from common.core.entity import Entity


def TestEntityEquality():
    """
    Core tests for entities.

    Entities are compared by its keys,
    regardless of other entity attributes.
    """
    e1 = Entity("test_entity1")
    e2 = Entity("test_entity2")
    same_as_e1 = Entity("test_entity1")

    same_as_e1.other_stuff = "Other Stuff"

    assert not e1 == e2
    assert e2 != e1
    assert e1 == same_as_e1
    assert not same_as_e1 != e1
