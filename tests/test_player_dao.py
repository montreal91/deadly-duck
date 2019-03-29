
"""
Tests for player and player dao classes.

Created Mar 27, 2019

@author montreal91
"""

import random

from app.data.game.player import DdDaoPlayer
from tests.flask_test_base import FlaskBaseTestCase


class DdDaoPlayerTestCase(FlaskBaseTestCase):
    """Tests for methods of DdDaoPlayer class."""

    def setUp(self):
        super().setUp()
        self.dao = DdDaoPlayer()

    def test_create_player(self):
        """Basic checks for one player creation."""

        random.seed(42)
        player = self.dao.CreatePlayer(
            career_pk=1, club_pk=1, level=1, age=16,
        )

        # Check that this player is not saved in the database.
        self.assertTrue(player.pk is None)

        self.assertEqual(player.first_name_c, "Blair")
        self.assertEqual(player.second_name_c, "Alice")
        self.assertEqual(player.last_name_c, "Wood")
        self.assertEqual(player.age_n, 16)

        self.assertEqual(player.career_pk, 1)
        self.assertEqual(player.club_pk, 1)

        self.assertEqual(player.level, 1)
        self.assertEqual(player.experience_n, 50)
        self.assertEqual(player.technique_n, 55)
        self.assertEqual(player.endurance_n, 50)
        self.assertEqual(player.max_stamina, 50)
        self.assertEqual(player.exhaustion_n, 0)


        player = self.dao.CreatePlayer(
            career_pk=2, club_pk=2, level=10, age=20,
        )

        self.assertTrue(player.pk is None)

        self.assertEqual(player.first_name_c, "Justine")
        self.assertEqual(player.second_name_c, "Joana")
        self.assertEqual(player.last_name_c, "Edgemon")
        self.assertEqual(player.age_n, 20)

        self.assertEqual(player.career_pk, 2)
        self.assertEqual(player.club_pk, 2)

        self.assertEqual(player.level, 10)
        self.assertEqual(player.experience_n, 2750)
        self.assertEqual(player.technique_n, 55)
        self.assertEqual(player.endurance_n, 95)
        self.assertEqual(player.max_stamina, 95)
        self.assertEqual(player.exhaustion_n, 0)

    def test_create_initial_club_players(self):
        """Checks for career initial player creation."""

        players = self.dao.CreateInitialClubPlayers(career_pk=1, club_pk=2)

        for i in range(len(players)):
            self.assertEqual(players[i].career_pk, 1)
            self.assertEqual(players[i].club_pk, 2)
            self.assertEqual(players[i].level, i)
