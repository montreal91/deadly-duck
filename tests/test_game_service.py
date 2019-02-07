
"""Tests for game logic.

Created Feb 03, 2019

@author montreal91
"""

from app.data.game.career import DdCareer
from app.data.game.club import DdDaoClub
from app.data.game.game_service import DdGameService
from app.data.game.match import DdMatch
from app.data.game.player import DdPlayer
from app.exceptions import BadUserInputException
from flask_test_base import FlaskBaseTestCase


class GameServiceTestCase(FlaskBaseTestCase):
    """Game logic test cases."""

    _EXPECTED_PLAYERS_IN_CLUB = 5

    def setUp(self):
        super().setUp()
        self._dao_club = DdDaoClub()
        self._service = DdGameService()
        self._service.InsertClubs()

    def test_start_new_career_positive(self):
        """Correct creation of the new career."""

        club_pks = self._dao_club.GetListOfClubPrimaryKeys()
        self._service.StartNewCareer(
            user_pk=self.user_pk, managed_club_pk=club_pks[0]
        )
        self._service.StartNewCareer(
            user_pk=self.user_pk, managed_club_pk=club_pks[-1]
        )
        careers = DdCareer.query.all()
        self.assertEquals(len(careers), 2)

        career1 = careers[0]
        career2 = careers[1]

        # Check if careers are created for correct user
        self.assertEqual(career1.user_pk, self.user_pk)
        self.assertEqual(career2.user_pk, self.user_pk)

        # Check if careers are created for correct clubs
        self.assertEqual(career1.managed_club_pk, club_pks[0])
        self.assertEqual(career2.managed_club_pk, club_pks[-1])

        # Just in case check that their pks are not equal
        self.assertNotEqual(career1.pk, career2.pk)

        # Check default parameters
        self.assertEqual(career1.season_n, 0)
        self.assertEqual(career1.day_n, 0)
        self.assertEqual(career2.season_n, 0)
        self.assertEqual(career2.day_n, 0)

        # Check that no players are created
        self.assertEqual(DdPlayer.query.count(), 0)

        # Check that there are no matches
        self.assertEqual(DdMatch.query.count(), 0)

    def test_start_new_career_negative(self):
        """This test specifies what should happen if data is incorrect."""

        club_pks = self._dao_club.GetListOfClubPrimaryKeys()

        # Try to create career with incorrect user
        with self.assertRaises(BadUserInputException):
            self._service.StartNewCareer(
                user_pk=self.user_pk + 10, managed_club_pk=club_pks[0]
            )
        self._abscence_check()

        # Try to create career with incorrect club
        with self.assertRaises(BadUserInputException):
            self._service.StartNewCareer(
                user_pk=self.user_pk, managed_club_pk=max(club_pks) + 10
            )
        self._abscence_check()

        # Just in case
        with self.assertRaises(BadUserInputException):
            self._service.StartNewCareer(
                user_pk=self.user_pk + 10, managed_club_pk=max(club_pks) + 10
            )
        self._abscence_check()

    def _abscence_check(self):
        # Make sure that no new careers are created
        self.assertEqual(DdMatch.query.count(), 0)

        # Make sure that no new players are created
        self.assertEqual(DdPlayer.query.count(), 0)

        # Make sure that no new matches are created
        self.assertEqual(DdCareer.query.count(), 0)
