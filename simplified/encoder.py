
"""
Created Apr 21, 2019

@author montreal91
"""

from json import JSONEncoder


class DduckJsonEncoder(JSONEncoder):
    """Simple encoder for game objects."""

    def default(self, obj):
        if hasattr(obj, "json"):
            return obj.json
        return super().default(obj)
