
"""Small module to make saves aware of transactions.

Created Feb 03, 2019

@author: montreal91
"""

from typing import Any
from typing import List

from app import db

def AbortChanges():
    """Rolls back the current session."""
    db.session.rollback()

def SaveObject(obj: Any):
    """Saves one object within one transaction."""
    db.session.add(obj)
    db.session.commit()


def SaveObjects(objects: List[Any]):
    """Saves many objects within one transaction."""
    db.session.add_all(objects)
    db.session.commit()
