
"""Crunching gameplay numbers.

Created on on 13 Sep 2018

@author: montreal91
"""
from unittest import TestCase

from app.data.game.player import DdPlayer
from app.data.game.player import PlayerModelComparator
from app.game.match_processor import DdMatchProcessor
from app.game.match_processor import LinearProbabilityFunction
from app.game.match_processor import NaiveProbabilityFunction
from configuration.config_game import DdGameplayConstants


class RegularTournamentTestCase(TestCase):
    """Test case class for crunching gameplay numbers."""

    def setUp(self):
        self._club1 = []
        self._club2 = []

        for i in range(5):
            p1 = DdPlayer(
                technique_n=50, endurance_n=50, experience_n=0, exhaustion_n=0
            )
            p1.age_n = DdGameplayConstants.STARTING_AGE.value + i
            p1.current_stamina_n = p1.max_stamina
            p1.matches = 0
            p1.sets = 0
            p1.games = 0
            self._club1.append(p1)

            p2 = DdPlayer(
                technique_n=50, endurance_n=50, experience_n=0, exhaustion_n=0
            )
            p2.age_n = DdGameplayConstants.STARTING_AGE.value + i
            p2.current_stamina_n = p2.max_stamina
            p2.matches = 0
            p2.sets = 0
            p2.games = 0
            self._club2.append(p2)

    def test_default(self):
        """Test tournament without exhaustion."""
        print()
        self._run_one_season(
            matches_to_play=44,
            recovery_day=3,
            exhaustion_per_set=0,
            recovery_function=current_recovery,
        )

        print("\nClub 1:")
        for player in self._club1:
            self._print_player(player)

        print("\nClub 2:")
        for player in self._club2:
            self._print_player(player)

    def test_exhausted(self):
        """Test tournament with exhaustion."""
        print()

        self._run_one_season(
            matches_to_play=44,
            recovery_day=3,
            exhaustion_per_set=4,
            recovery_function=exhausted_recovery,
        )

        print("\nClub 1:")
        for player in self._club1:
            self._print_player(player)

        print("\nClub 2:")
        for player in self._club2:
            self._print_player(player)


    def _print_player(self, player):
        string = (
            "Lvl: {lvl:2d}| "
            "Age:{age:2d}| "
            "Tech: {tech:3d}| "
            "Endr: {endr:3d}| "
            "Exh: {exh:2d}| "
            "Exp: {exp:4d}| "
            "Match: {match:2d}| "
            "Sets: {sets:2d}| "
            "Games: {games:3d}| "
        )
        print(string.format(
            lvl=player.level,
            age=player.age_n,
            tech=player.technique_n,
            endr=player.endurance_n,
            exh=player.exhaustion_n,
            exp=player.experience_n,
            match=player.matches,
            sets=player.sets,
            games=player.games,
        ))


    def _recover(self, recover_function):
        for player in self._club1:
            player.RecoverStamina(recover_function(player))

        for player in self._club2:
            player.RecoverStamina(recover_function(player))

    def _run_one_season(
            self,
            matches_to_play: int,
            recovery_day: int,
            exhaustion_per_set,
            recovery_function,
    ):
        day = 0

        home_stamina = 0
        away_stamina = 0

        while matches_to_play > 0:
            day += 1
            if day % recovery_day == 0:
                self._recover(recovery_function)
                continue


            p1 = max(self._club1, key=PlayerModelComparator)
            p2 = max(self._club2, key=PlayerModelComparator)

            mp = DdMatchProcessor(LinearProbabilityFunction)
            res = mp.ProcessMatch(p1, p2)

            home_experience = DdPlayer.CalculateNewExperience(res.home_sets, p2)
            away_experience = DdPlayer.CalculateNewExperience(res.away_sets, p1)


            p1.AddExperience(home_experience)
            p1.LevelUpAuto()
            p2.AddExperience(away_experience)
            p2.LevelUpAuto()

            p1.RemoveStaminaLostInMatch(res.home_stamina_lost)
            p2.RemoveStaminaLostInMatch(res.away_stamina_lost)
            home_stamina += res.home_stamina_lost
            away_stamina += res.away_stamina_lost

            p1.exhaustion_n += res.home_sets * exhaustion_per_set
            p2.exhaustion_n += res.away_sets * exhaustion_per_set

            p1.matches += 1
            p1.sets += res.home_sets
            p1.games += res.home_games
            p2.matches += 1
            p2.sets += res.away_sets
            p2.games += res.away_games

            self._recover(recovery_function)

            matches_to_play -= 1

        for i in range(5):
            self._club1[i].RecoverStamina(self._club1[i].max_stamina)
            self._club2[i].RecoverStamina(self._club2[i].max_stamina)

        print(f"Average stamina per match {home_stamina / 44}")


def current_recovery(player: DdPlayer) -> int:
    return DdGameplayConstants.STAMINA_RECOVERY_PER_DAY.value


def exhausted_recovery(player: DdPlayer) -> int:
    base = player.max_stamina
    res = base * (100 - player.exhaustion_n) / 100
    return int(round(res))
