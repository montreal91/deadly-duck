
from typing import Any
from typing import List
from unittest import TestCase

from app import CreateApp
from app import db
from app.data.main.user import DdUser

class FlaskBaseTestCase(TestCase):
    """Class for common manipulations with flask and database objects."""
    def setUp(self):
        self.app = CreateApp("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        user = DdUser(social_pk="Social")
        self.SaveTestObject(user)
        self.user_pk = user.pk

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def SaveTestObject(self, obj: Any):
        """Saves one object in test database."""

        db.session.add(obj)
        db.session.commit()

    def SaveTestObjects(self, objects: List[Any]):
        """Saves list of objects in test database."""

        db.session.add_all(objects)
        db.session.commit()
