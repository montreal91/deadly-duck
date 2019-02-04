"""Tests for playoffs and everything relevant to it.

Created: Feb 02, 2019

@author: montreal91
"""

from app.data.game.career import DdCareer
from app.data.game.game_service import DdGameService
from app.data.game.match import DdMatch, DdMatchStatuses
from app.data.game.playoff_series import DdPlayoffSeries
from app.data.main.user import DdUser

from flask_test_base import FlaskBaseTestCase


class PlayoffSeriesTestCase(FlaskBaseTestCase):
    """Unit tests for playoff series."""

    def setUp(self):
        super().setUp()
        self._service = DdGameService()
        self._service.InsertClubs()

        career = DdCareer(user_pk=self.user_pk, managed_club_pk=1)
        self.SaveTestObject(career)

        series = DdPlayoffSeries()
        series.top_seed_pk = 1
        series.low_seed_pk = 9
        series.career_pk = career.pk
        series.season_n = career.season_n

        self.SaveTestObject(series)

        self.series_pk = series.pk

    def test_basics(self):
        series = DdPlayoffSeries.query.get(self.series_pk)
        self.assertTrue(series is not None)
