
"""
Created 2019.12.09

@author montreal91
"""


from unittest import TestCase

from attr import Factory
from attr import s


@s(auto_attribs=True)
class Entity:
    """Basic class for entities."""

    NO_KEY = ""

    key: str = Factory(str)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    def __ne__(self, other):
        return not self == other


class EntityTestCase(TestCase):
    def test_entity_equality(self):
        """
        Core tests for entities.

        Entities are compared by its keys,
        regardless of other entity attributes.
        """

        e1 = Entity("test_entity1")
        e2 = Entity("test_entity2")

        same_as_e1 = Entity("test_entity1")
        same_as_e1.other_stuff = "Other Stuff"

        self.assertFalse(e1 == e2)
        self.assertTrue(e2 != e1)
        self.assertTrue(e1 == same_as_e1)
        self.assertFalse(same_as_e1 != e1)
