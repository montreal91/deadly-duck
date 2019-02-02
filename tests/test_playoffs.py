"""Tests for playoffs and everything relevant to it.

Created: Feb 02, 2019

@author: montreal91
"""

from unittest import TestCase

from app import CreateApp
from app import db
from app.data.game.game_service import DdGameService
from app.data.game.match import DdMatch, DdMatchStatuses
from app.data.game.playoff_series import DdPlayoffSeries


class PlayoffSeriesTestCase(TestCase):
    """Unit tests for playoff series."""

    def setUp(self):
        self.app = CreateApp("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._service = DdGameService()
        self._service.InsertClubs()

        series = DdPlayoffSeries()
        series.top_seed_pk = 1
        series.low_seed_pk = 9
        series.season_n = 1
        series.is_finished = False

        db.session.add(series)
        db.session.commit()
        self.series_pk = series.pk
        self._service._CreateMatchesForSeriesList([series], 1)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_basics(self):
        series = DdPlayoffSeries.query.get(self.series_pk)
        self.assertEqual(len(series.matches), 7)

        for match in series.matches:
            self.assertEqual(match.status_en, DdMatchStatuses.planned)

        self.assertEqual(series.GetTopSeedMatchesWon(2), 0)
        self.assertEqual(series.GetLowSeedMatchesWon(2), 0)
        self.assertTrue(
            series.GetWinnerPk(sets_to_win=2, matches_to_win=4) is None
        )
