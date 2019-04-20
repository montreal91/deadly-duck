
"""
Created Apr 09, 2019

@author montreal91
"""

from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple

from configuration.config_game import DdGameplayConstants
from simplified.club import DdClub
from simplified.match import DdMatchProcessor
from simplified.match import DdMatchResult
from simplified.match import DdScheduledMatchStruct
from simplified.match import DdStandingsRowStruct
from simplified.match import LinearProbabilityFunction
from simplified.player import DdPlayer
from simplified.player import DdPlayerFactory
from simplified.player import ExhaustedRecovery


class DdGameParams(NamedTuple):
    """Passive class to store game parameters"""

    exhaustion_per_set: int
    matches_to_play: int
    recovery_day: int


class DdGameDuck:
    """A class that incapsulates the game logic."""

    def __init__(self, params: DdGameParams):
        self._day = 0
        self._history = []
        self._last_score = ""
        self._params = params
        self._player_factory = DdPlayerFactory()
        self._results = []
        self._schedule = []
        self._season = 1
        self._selected_player = False
        self._users_club = 0

        self._clubs = []
        self._clubs.append(DdClub(name="Auckland Aces"))
        self._clubs.append(DdClub(name="Western Fury"))

        for i in range(5):
            age = DdGameplayConstants.STARTING_AGE.value + i

            self._clubs[0].AddPlayer(
                self._player_factory.CreatePlayer(age=age, level=i*2)
            )
            self._clubs[1].AddPlayer(
                self._player_factory.CreatePlayer(age=age, level=i*2)
            )
        self._MakeSchedule()

    @property
    def context(self) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        return dict(
            day=self._day,
            is_recovery_day=self._IsRecoveryDay(),
            last_score=self._last_score,
            opponent=self._opponent,
            remaining_matches=len(self._remaining_matches),
            standings=self._standings,
            user_players=self._clubs[self._users_club].players,
        )

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        return self._day >= len(self._schedule)

    def SelectPlayer(self, i: int):
        """Sets selected player for user."""

        assert 0 <= i < len(self._clubs[self._users_club].players)
        self._clubs[self._users_club].SelectPlayer(i)
        self._selected_player = True

    def SetPractice(self, i1: int, i2: int):
        """Sets a practice match between two selected players."""

        self._clubs[self._users_club].SetPractice(i1, i2)

    def Update(self):
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """

        if self._selected_player is False and not self._IsRecoveryDay():
            return False

        self._PlayOneDay()
        self._selected_player = False
        self._day += 1

        if self.season_over:
            self._NextSeason()
        return True

    def _GetClubSchedule(self, club_pk):
        for day in self._schedule:
            if day is None:
                continue
            for match in day:
                if match.is_played:
                    continue
                if match.home_pk == club_pk or match.away_pk == club_pk:
                    yield match

    def _IsRecoveryDay(self):
        return self._day % self._params.recovery_day == 0

    def _MakeSchedule(self):
        day = -1
        done = 0
        while done < self._params.matches_to_play:
            day += 1
            if day % self._params.recovery_day == 0:
                self._schedule.append(None)
                continue

            if done % 2 == 0:
                self._schedule.append((DdScheduledMatchStruct(0, 1),))
            else:
                self._schedule.append((DdScheduledMatchStruct(1, 0),))
            done += 1
        self._schedule.append(None)

    def _NextSeason(self):
        max_players_in_club = DdGameplayConstants.MAX_PLAYERS_IN_CLUB.value
        for club in self._clubs:
            for player in club.players:
                player.AgeUp()
                player.AfterSeasonRest()
            club.ExpelRetiredPlayers()

            while len(club.players) < max_players_in_club:
                club.AddPlayer(self._player_factory.CreatePlayer(
                    age=DdGameplayConstants.STARTING_AGE.value,
                    level=0,
                ))
            club.SortPlayers()

        self._day = 0
        self._season += 1

        self._history.append(self._standings)
        self._results = []
        self._last_score = ""
        self._schedule = []
        self._MakeSchedule()

    def _Recover(self, recover_function):
        for club in self._clubs:
            for player in club.players:
                player.RecoverStamina(recover_function(player))

    def _PlayOneDay(self):
        for match in self._practice_matches:
            self._ProcessMatch(match[0], match[1], practice=True)

        for club in self._clubs:
            club.UnsetPractice()

        day = self._schedule[self._day]
        if day is None:
            return

        day_results = []
        for match in day:
            res = self._ProcessMatch(
                self._clubs[match.home_pk].selected_player,
                self._clubs[match.away_pk].selected_player,
            )
            match.is_played = True

            res.home_pk = match.home_pk
            res.away_pk = match.away_pk
            day_results.append(res)

        self._results.append(day_results)

    @property
    def _opponent(self):
        if self._IsRecoveryDay():
            return None

        def ScheduleFilter(pair: DdScheduledMatchStruct):
            return pair.home_pk == self._users_club

        schedule = self._schedule[self._day]
        planned_match = [pair for pair in schedule if ScheduleFilter(pair)]

        if planned_match:
            return self._clubs[planned_match[0].away_pk].selected_player
        return None

    @property
    def _practice_matches(self):
        for club in self._clubs:
            if club.practice_match is not None:
                yield club.practice_match

    @property
    def _remaining_matches(self):
        return list(self._GetClubSchedule(self._users_club))

    @property
    def _standings(self) -> List[DdStandingsRowStruct]:
        results = [DdStandingsRowStruct(club.name) for club in self._clubs]

        for day in self._results:
            for match in day:
                results[match.home_pk].sets_won += match.home_sets
                results[match.home_pk].games_won += match.home_games

                results[match.away_pk].sets_won += match.away_sets
                results[match.away_pk].games_won += match.away_games

        return results

    def _ProcessMatch(
        self, plr1: DdPlayer, plr2: DdPlayerFactory, practice: bool = False
    ) -> DdMatchResult:
        mp = DdMatchProcessor(LinearProbabilityFunction)
        res = mp.ProcessMatch(plr1, plr2, 1 if practice else 2)

        home_experience = DdPlayer.CalculateNewExperience(res.home_sets, plr2)
        away_experience = DdPlayer.CalculateNewExperience(res.away_sets, plr1)


        plr1.AddExperience(home_experience)
        plr2.AddExperience(away_experience)
        plr1.RemoveStaminaLostInMatch(res.home_stamina_lost)
        plr2.RemoveStaminaLostInMatch(res.away_stamina_lost)

        exhaustion = res.home_sets + res.away_sets
        exhaustion *= self._params.exhaustion_per_set

        plr1.AddExhaustion(exhaustion)
        plr2.AddExhaustion(exhaustion)

        self._Recover(ExhaustedRecovery)

        self._last_score = res.full_score

        return res
