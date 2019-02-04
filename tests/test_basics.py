
from unittest import TestCase

from flask import current_app

from flask_test_base import FlaskBaseTestCase


class BasicsTestCase(FlaskBaseTestCase):
    def test_app_exists(self):
        self.assertFalse(current_app is None)


    def test_app_is_testing(self):
        self.assertTrue(current_app.config["TESTING"])
