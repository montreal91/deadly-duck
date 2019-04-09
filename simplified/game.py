
"""
Created Apr 09, 2019

@author montreal91
"""

import json

from random import choice
from typing import Any
from typing import Dict

from configuration.config_game import DdGameplayConstants
from simplified.club import DdClub
from simplified.match import DdMatchProcessor
from simplified.match import DdScheduledMatchStruct
from simplified.match import DdStandingsRowStruct
from simplified.match import LinearProbabilityFunction
from simplified.player import DdPlayer
from simplified.player import ExhaustedRecovery


class DdGameDuck:
    """A class that incapsulates game logic."""

    def __init__(self):
        self._day = 0
        self._recovery_day = 3
        self._exhaustion_per_set = 4
        self._selected_player = False
        self._last_score = ""
        self._schedule = []
        self._MakeSchedule(10)
        self._results = []
        self._users_club = 0

        with open("configuration/names.json", "r") as names_file:
            self._names = json.load(names_file)

        self._clubs = []
        self._clubs.append(DdClub(name="Auckland Aces"))
        self._clubs.append(DdClub(name="Western Fury"))

        for i in range(5):
            age = DdGameplayConstants.STARTING_AGE.value + i

            self._clubs[0].AddPlayer(self._MakePlayer(age, i * 200))
            self._clubs[1].AddPlayer(self._MakePlayer(age, i * 200))

    @property
    def context(self) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        return dict(
            day=self._day,
            is_recovery_day=self._IsRecoveryDay(),
            last_score=self._last_score,
            remaining_matches=len(self._remaining_matches),
            standings=self._standings,
            user_players=self._clubs[self._users_club].players,
        )

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        return self._day >= len(self._schedule)

    def SelectPlayer(self, i):
        """Sets selected player for user."""

        assert 0 <= i < len(self._clubs[self._users_club].players)
        self._clubs[self._users_club].SelectPlayer(i)
        self._selected_player = True

    def Update(self):
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """
        if self._IsRecoveryDay():
            self._Recover(ExhaustedRecovery)
            self._day += 1
            return True

        if self._selected_player is False:
            return False

        self._PlayOneDay()
        self._selected_player = False
        self._day += 1
        return True

    def _GetSchedule(self, club_pk):
        for day in self._schedule:
            if day is None:
                continue
            for match in day:
                if match.is_played:
                    continue
                if match.home_pk == club_pk or match.away_pk == club_pk:
                    yield match

    def _IsRecoveryDay(self):
        return self._day % self._recovery_day == 0

    def _MakePlayer(self, age: int, experience: int) -> DdPlayer:
        player = DdPlayer(
            first_name=choice(self._names["names"]),
            second_name=choice(self._names["names"]),
            last_name=choice(self._names["surnames"]),
            technique=DdGameplayConstants.SKILL_BASE.value,
            endurance=DdGameplayConstants.SKILL_BASE.value,
            age=age,
        )

        player.AddExperience(experience)
        player.AfterSeasonRest()
        return player

    def _MakeSchedule(self, matches_to_play):
        day = -1
        done = 0
        while done < matches_to_play:
            day += 1
            if day % self._recovery_day == 0:
                self._schedule.append(None)
                continue

            self._schedule.append((DdScheduledMatchStruct(0, 1),))
            done += 1

    def _Recover(self, recover_function):
        for club in self._clubs:
            for player in club.players:
                player.RecoverStamina(recover_function(player))

    def _PlayOneDay(self):
        day = self._schedule[self._day]
        if day is None:
            return

        day_results = []
        for match in day:
            p1 = self._clubs[match.home_pk].selected_player
            p2 = self._clubs[match.away_pk].selected_player

            mp = DdMatchProcessor(LinearProbabilityFunction)
            res = mp.ProcessMatch(p1, p2)
            res.home_pk = match.home_pk
            res.away_pk = match.away_pk
            day_results.append(res)

            home_experience = DdPlayer.CalculateNewExperience(res.home_sets, p2)
            away_experience = DdPlayer.CalculateNewExperience(res.away_sets, p1)


            p1.AddExperience(home_experience)
            p2.AddExperience(away_experience)
            p1.RemoveStaminaLostInMatch(res.home_stamina_lost)
            p2.RemoveStaminaLostInMatch(res.away_stamina_lost)

            exhaustion = res.home_sets + res.away_sets
            exhaustion *= self._exhaustion_per_set

            p1.AddExhaustion(exhaustion)
            p2.AddExhaustion(exhaustion)

            self._Recover(ExhaustedRecovery)

            self._last_score = res.full_score
            match.is_played = True

        self._results.append(day_results)

    @property
    def _remaining_matches(self):
        return list(self._GetSchedule(self._users_club))

    @property
    def _standings(self):
        results = [DdStandingsRowStruct(club.name) for club in self._clubs]


        for day in self._results:
            for match in day:
                results[match.home_pk].sets_won += match.home_sets
                results[match.home_pk].games_won += match.home_games

                results[match.away_pk].sets_won += match.away_sets
                results[match.away_pk].games_won += match.away_games

        return results
