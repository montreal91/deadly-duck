
"""
Useful tools for simple json serialization and deserialization.

Created Jun 27, 2019

@author montreal91
"""

from json import JSONEncoder
from typing import Any
from typing import Dict
from typing import Tuple
from typing import NamedTuple
from typing import Optional


class DdField(NamedTuple):
    """Tuple that binds python object fields with json properties."""

    py_name: str
    json_name: str


class DdJsonable:
    """
    Base class for all json serializable and deserializable objects.

    Every descendant object should declare its own `_FIELD_MAP` tuple for
    correct serialization and deserialization.
    """

    _FIELD_MAP: Tuple[DdField, ...]

    def __from_json__(self, data: Dict[str, Any]):
        """Restores object from raw json data."""
        for field in self._FIELD_MAP:
            self.__dict__[field.py_name] = data[field.json_name]

    def __to_json__(self) -> Dict[str, Any]:
        """Converts object into an easily json-serializable dict."""
        data = {self.__class__.__name__: True}
        for field in self._FIELD_MAP:
            data[field.json_name] = self.__dict__[field.py_name]
        return data


class DdJsonEncoder(JSONEncoder):
    """Encoder for jsonable objects."""

    def default(self, o):
        if issubclass(type(o), DdJsonable):
            return o.__to_json__()
        return super().default(o)


class DdJsonDecoder:
    """Decoder for jsonable objects."""

    def __call__(self, obj):
        """Decodes an object if possible."""

        typename = self._GetTypeName(obj)
        if typename is not None:
            res = self._registry[typename]()
            res.__from_json__(obj)
            return res
        return obj

    def __init__(self):
        self._registry = {}

    def Register(self, some_type):
        """Marks class as serializable for the decoder."""

        self._registry[some_type.__name__] = some_type

    def _GetTypeName(self, obj) -> Optional[str]:
        for key in self._registry:
            if key in obj:
                return key
        return None
