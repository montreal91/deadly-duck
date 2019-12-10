
"""
Created 2019.12.09

@author montreal91
"""

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
