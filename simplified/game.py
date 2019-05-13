
"""
Created Apr 09, 2019

@author montreal91
"""

from random import shuffle
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from configuration.config_game import club_names
from configuration.config_game import DdGameplayConstants
from simplified.club import DdClub
from simplified.match import DdMatchProcessor
from simplified.match import DdMatchResult
from simplified.match import DdScheduledMatchStruct
from simplified.match import DdStandingsRowStruct
from simplified.player import DdPlayer
from simplified.player import DdPlayerFactory
from simplified.player import DdPlayerReputationCalculator


ScheduleDay = List[DdScheduledMatchStruct]


class DdGameParams(NamedTuple):
    """Passive class to store game parameters"""

    exdiv_matches: int
    exhaustion_function: Callable[[int], int]
    exhaustion_per_set: int
    indiv_matches: int

    # This value should be a power of two
    playoff_clubs: int

    probability_function: Callable[[float, float], float]
    recovery_day: int
    recovery_function: Callable[[DdPlayer], int]
    reputation_function: Callable[[int], int]
    starting_club: int


class DdGameDuck:
    """A class that incapsulates the game logic."""

    _clubs: List[DdClub]
    _day: int
    _history: List[List[DdStandingsRowStruct]]
    _params: DdGameParams
    _player_factory: DdPlayerFactory
    _results: List[List[DdMatchResult]]
    _schedule: List[Optional[List[DdScheduledMatchStruct]]]
    _selected_player: bool
    _users_club: int

    def __init__(self, params: DdGameParams):
        self._day = 0
        self._history = []
        self._params = params
        self._player_factory = DdPlayerFactory()
        self._results = []
        self._schedule = []
        self._selected_player = False
        self._users_club = params.starting_club

        self._clubs = []

        for club_name in club_names[1] + club_names[2]:
            self._AddClub(club_name=club_name)
        self._MakeSchedule()

    @property
    def context(self) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        return dict(
            day=self._day,
            is_recovery_day=self._IsRecoveryDay(),
            clubs=[club.name for club in self._clubs],
            last_results=self._last_results,
            opponent=self._opponent,
            remaining_matches=len(self._remaining_matches),
            standings=self._standings,
            user_players=self._clubs[self._users_club].players,
            users_club=self._users_club,
            history=self._history,
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

    def _AddClub(self, club_name: str):
        club = DdClub(name=club_name)
        max_players = 5
        for i in range(max_players):
            age = DdGameplayConstants.STARTING_AGE.value + i

            club.AddPlayer(
                self._player_factory.CreatePlayer(age=age, level=i*2)
            )
        self._clubs.append(club)

    def _GetClubSchedule(self, club_pk):
        for day in self._schedule:
            if day is None:
                continue
            for match in day:
                if match.is_played:
                    continue
                if match.home_pk == club_pk or match.away_pk == club_pk:
                    yield match

    def _IsRecoveryDay(self) -> bool:
        return self._schedule[self._day] is None

    def _MakeFullSchedule(self, pk_list: List[int]):
        def MirrorDay(matches: List[DdScheduledMatchStruct]):
            return [
                DdScheduledMatchStruct(m.away_pk, m.home_pk) for m in matches
            ]

        def CopyDay(matches):
            return [
                DdScheduledMatchStruct(m.home_pk, m.away_pk) for m in matches
            ]

        def ComposeDays(matches: List[DdScheduledMatchStruct], n: int):
            res = []
            for i in range(n // 2):
                res.append(CopyDay(matches))
            for i in range(n // 2):
                res.append(MirrorDay(matches))
            return res

        basic_schedule = _MakeBasicSchedule(pk_list)

        res: List[ScheduleDay] = []
        in_div = self._params.indiv_matches
        ex_div = self._params.exdiv_matches

        for i in range(len(basic_schedule)):
            if i % 2 == 0:
                res.extend(ComposeDays(basic_schedule[i], ex_div))
            else:
                res.extend(ComposeDays(basic_schedule[i], in_div))
        return res

    def _MakeSchedule(self):
        pk_list = list(range(len(self._clubs)))
        shuffle(pk_list)
        days = self._MakeFullSchedule(pk_list)
        shuffle(days)

        day = -1
        done = 0
        while done < len(days):
            day += 1
            if day % self._params.recovery_day == 0:
                self._schedule.append(None)
                continue

            self._schedule.append(days[done])
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

        self._history.append(self._standings)
        self._results = []
        self._schedule = []
        self._MakeSchedule()

    def _PerformPractice(self):
        for club in self._clubs:
            club.PerformPractice()

    def _Recover(self):
        for club in self._clubs:
            for player in club.players:
                player.RecoverStamina(self._params.recovery_function(player))

    def _PlayOneDay(self):
        day = self._schedule[self._day]
        if day is None:
            self._PerformPractice()
            self._Recover()
            return

        day_results = []
        for match in day:
            res = self._match_processor.ProcessMatch(
                self._clubs[match.home_pk].selected_player,
                self._clubs[match.away_pk].selected_player,
            )
            match.is_played = True

            res.home_pk = match.home_pk
            res.away_pk = match.away_pk
            day_results.append(res)

        self._results.append(day_results)
        self._Recover()

    @property
    def _last_results(self) -> List[DdMatchResult]:
        if not self._results:
            return []

        return self._results[-1]

    @property
    def _match_processor(self) -> DdMatchProcessor:
        def ExhaustionFunction(sets: int) -> int:
            base = self._params.exhaustion_function(sets)
            return base * self._params.exhaustion_per_set
        return DdMatchProcessor(
            games_to_win=6,
            sets_to_win=2,
            exhaustion_function=ExhaustionFunction,
            probability_function=self._params.probability_function,
            reputation_function=self._params.reputation_function,
        )

    @property
    def _opponent(self) -> Optional[Tuple[str, DdPlayer]]:
        if self._IsRecoveryDay():
            return None

        def ScheduleFilter(pair: DdScheduledMatchStruct):
            return pair.home_pk == self._users_club

        schedule = self._schedule[self._day]

        # Just in case
        if schedule is None:
            return None
        planned_match = [pair for pair in schedule if ScheduleFilter(pair)]

        if planned_match:
            opponent_club = self._clubs[planned_match[0].away_pk]
            return (
                opponent_club.name,
                opponent_club.selected_player
            )
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
        results = [DdStandingsRowStruct(i) for i in range(len(self._clubs))]

        for day in self._results:
            for match in day:
                results[match.home_pk].sets_won += match.home_sets
                results[match.home_pk].games_won += match.home_games

                results[match.away_pk].sets_won += match.away_sets
                results[match.away_pk].games_won += match.away_games

        return results


def _MakeBasicSchedule(pk_list: List[int]):
    def MakePairs(lst: List[int]) -> ScheduleDay:
        n = len(lst) - 1
        mid = len(lst) // 2
        return [DdScheduledMatchStruct(lst[i], lst[n-i]) for i in range(mid)]

    def Shift(lst: List[int], n: int) -> List[int]:
        if n == 0:
            return list(lst)
        return [lst[0]] + lst[-n:] + lst[1:-n]

    def ShiftGen(lst: List[int]) -> Generator[List[int], None, None]:
        for i in range(len(lst) - 1):
            yield Shift(lst, i)

    return [MakePairs(l) for l in ShiftGen(pk_list)]
