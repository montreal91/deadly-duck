
from unittest import TestCase

from app.data.game.player import DdPlayer
from app.data.game.player import PlayerModelComparator
from app.game.match_processor import DdMatchProcessor
from configuration.config_game import DdGameplayConstants


class RoundTournamentTestCase(TestCase):
    def setUp(self):
        self._club1 = []
        self._club2 = []

        for i in range(5):
            p1 = DdPlayer(technique_n=50, endurance_n=50, experience_n=0)
            p1.age_n = DdGameplayConstants.STARTING_AGE.value + i
            p1.current_stamina_n = p1.max_stamina
            p1.matches = 0
            self._club1.append(p1)

            p2 = DdPlayer(technique_n=50, endurance_n=50, experience_n=0)
            p2.age_n = DdGameplayConstants.STARTING_AGE.value + i
            p2.current_stamina_n = p2.max_stamina
            p2.matches = 0
            self._club2.append(p2)


    def test1(self):
        print()
        for player in self._club1:
            self._print_player(player)
        print()
        for player in self._club2:
            self._print_player(player)


    def test2(self):
        print()

        matches_to_play = 44
        day = 0

        while matches_to_play > 0:
            day += 1
            if day % 3 == 0:
                self._recover()
                continue


            p1 = max(self._club1, key=PlayerModelComparator)
            p2 = max(self._club2, key=PlayerModelComparator)

            mp = DdMatchProcessor()
            res = mp.ProcessMatch(p1, p2)

            home_experience = DdPlayer.CalculateNewExperience(res.home_sets, p2)
            away_experience = DdPlayer.CalculateNewExperience(res.away_sets, p1)

            p1.AddExperience(home_experience)
            p1.LevelUpAuto()
            p2.AddExperience(away_experience)
            p2.LevelUpAuto()

            p1.RemoveStaminaLostInMatch(res.home_stamina_lost)
            p2.RemoveStaminaLostInMatch(res.away_stamina_lost)

            p1.matches += 1
            p2.matches += 1

            self._recover()

            matches_to_play -= 1

        for i in range(5):
            self._club1[i].RecoverStamina(self._club1[i].max_stamina)
            self._club2[i].RecoverStamina(self._club2[i].max_stamina)

        print("\nClub 1:")
        for player in self._club1:
            self._print_player(player)

        print("\nClub 2:")
        for player in self._club2:
            self._print_player(player)


    def _print_player(self, player):
        print("Lvl: {0:2d} Age:{1:2d} Tch: {2:3d} Enr: {3:3d} Exp: {4:4d} Mat: {5:2d}".format(
            player.level,
            player.age_n,
            player.technique_n,
            player.endurance_n,
            player.experience_n,
            player.matches,
        ))


    def _recover(self):
        for player in self._club1:
            player.RecoverStamina(DdGameplayConstants.STAMINA_RECOVERY_PER_DAY.value)

        for player in self._club2:
            player.RecoverStamina(DdGameplayConstants.STAMINA_RECOVERY_PER_DAY.value)
