
"""
Created Apr 09, 2019

@author montreal91
"""

import json

from random import choice
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

from configuration.config_game import DdGameplayConstants
from simplified.club import DdClub
from simplified.competition import DdAbstractCompetition
from simplified.match import DdMatchResult
from simplified.match import DdScheduledMatchStruct
from simplified.match import DdStandingsRowStruct
from simplified.player import DdCourtSurface
from simplified.player import DdPlayer
from simplified.player import DdPlayerFactory
from simplified.playoffs import DdPlayoff
from simplified.playoffs import DdPlayoffParams
from simplified.regular_championship import DdChampionshipParams
from simplified.regular_championship import DdRegularChampionship


class DdGameParams(NamedTuple):
    """Passive class to store game parameters"""

    championship_params: DdChampionshipParams
    playoff_params: DdPlayoffParams
    recovery_function: Callable[[DdPlayer], int]
    starting_club: int


class DdOpponentStruct:
    """Passive class to store information about opponent for the next match."""
    club_name: str
    match_surface: str
    player: Optional[DdPlayer]


class DdGameDuck:
    """A class that incapsulates the game logic."""

    _SURFACES = (
        DdCourtSurface.CLAY,
        DdCourtSurface.GRASS,
        DdCourtSurface.HARD,
    )

    _clubs: Dict[int, DdClub]
    _competition: DdAbstractCompetition
    _history: List[Dict[str, Any]]
    _params: DdGameParams
    _player_factory: DdPlayerFactory
    _results: List[DdMatchResult]

    def __init__(self, params: DdGameParams):
        self._history = [{}]
        self._params = params
        self._player_factory = DdPlayerFactory()
        self._results = []

        self._clubs = {}

        with open("configuration/clubs.json", "r") as data_file:
            club_data = json.load(data_file)

        for pk, club in enumerate(club_data):
            self._AddClub(
                pk=pk, club_name=club["name"], surface=club["surface"]
            )

        self._clubs[self._params.starting_club].SetControlled(True)

        self._competition = DdRegularChampionship(
            self._clubs, self._params.championship_params
        )

    @property
    def context(self) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        return dict(
            day=self._competition.day,
            clubs=[club.name for club in self._clubs.values()],
            last_results=self._last_results,
            opponent=self._GetOpponent(self._params.starting_club),
            remaining_matches=self._competition.GetClubSchedule(
                self._params.starting_club
            ),
            standings=self._standings,
            user_players=self._user_players,
            users_club=self._params.starting_club,
            history=self._history,
            title=self._competition.title,
        )

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        return self._competition.title == "Cup" and self._competition.is_over

    def FirePlayer(self, i: int, pk: int):
        """Fires the selected player from user's club."""

        assert 0 <= pk < len(self._clubs), "Incorrect club index."

        assert i >= 0, "Player index should be positive."
        assert i < len(self._clubs[pk].players), (
            "There is no player with such index in your club."
        )
        self._clubs[pk].PopPlayer(i)

    def HirePlayer(self, surface: str, pk: int):
        """Hires a new player for user's club."""

        assert 0 <= pk < len(self._clubs), "Incorrect club index."

        choices = "|".join(self._SURFACES)
        assert surface in self._SURFACES, (
            "You can't choose such speciality. "
            "Choices are: "
            f"{choices}"
        )
        player = self._player_factory.CreatePlayer(
            level=0,
            age=DdGameplayConstants.STARTING_AGE.value,
            speciality=surface
        )
        self._clubs[pk].AddPlayer(player)

    def SelectPlayer(self, i: int, pk: int):
        """Sets selected player for user."""

        assert 0 <= pk < len(self._clubs), "Incorrect club index."
        assert 0 <= i < len(self._clubs[pk].players), (
            "Incorrect player index."
        )
        self._clubs[pk].SelectPlayer(i)

    def Update(self):
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """

        if self._decision_required:
            return False

        self._PlayOneDay()
        self._Unselect()

        if self.season_over:
            self._NextSeason()

        if self._competition.is_over:
            self._SaveHistory()
            self._StartPlayoff()
        return True

    @property
    def _decision_required(self) -> bool:
        if self._competition.current_matches is None:
            return False
        for match in self._competition.current_matches:
            if self._clubs[match.home_pk].needs_decision:
                return True
            if self._clubs[match.away_pk].needs_decision:
                return True
        return False

    @property
    def _last_results(self) -> List[DdMatchResult]:
        if not self._results:
            return []

        return self._results

    @property
    def _standings(self) -> List[DdStandingsRowStruct]:
        standings = self._competition.standings
        if standings:
            return standings
        return [DdStandingsRowStruct(i) for i in range(len(self._clubs))]

    @property
    def _user_players(self) -> List[DdPlayer]:
        for club in self._clubs.values():
            if club.is_controlled:
                return club.players
        return []

    def _AddClub(self, pk: int, club_name: str, surface: str):
        club = DdClub(name=club_name, surface=surface)
        max_players = 5
        for i in range(max_players):
            age = DdGameplayConstants.STARTING_AGE.value + i

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=age, level=i*2, speciality=choice(self._SURFACES)
            ))
        self._clubs[pk] = club

    def _NextSeason(self):
        for i in range(len(self._clubs)):
            club: DdClub = self._clubs[i]
            for player in club.players:
                player.AgeUp()
                player.AfterSeasonRest()
            club.ExpelRetiredPlayers()

            if club.is_controlled:
                continue

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=0,
                speciality=club.surface
            ))
            club.AddPlayer(self._player_factory.CreatePlayer(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=0,
                speciality=choice(self._SURFACES),
            ))

        self._SaveHistory()
        self._competition = DdRegularChampionship(
            self._clubs,
            self._params.championship_params
        )
        self._history.append({})

    def _PerformPractice(self):
        for club in self._clubs.values():
            club.PerformPractice()

    def _Recover(self):
        for club in self._clubs.values():
            for player in club.players:
                player.RecoverStamina(self._params.recovery_function(player))

    def _PlayOneDay(self):
        self._results = self._competition.Update()

        if self._results is None:
            self._PerformPractice()

        self._Recover()

    def _SaveHistory(self):
        self._history[-1][self._competition.title] = self._competition.standings

    def _StartPlayoff(self):
        self._competition = DdPlayoff(
            self._clubs,
            self._params.playoff_params,
            self._competition.standings,
        )

    def _Unselect(self):
        for club in self._clubs.values():
            club.SelectPlayer(None)

    def _GetOpponent(self, pk: int) -> Optional[DdOpponentStruct]:
        def ScheduleFilter(pair: DdScheduledMatchStruct):
            if pair.home_pk == pk:
                return True
            return pair.away_pk == pk

        schedule = self._competition.current_matches

        # Just in case
        if schedule is None:
            return None
        planned_match = [pair for pair in schedule if ScheduleFilter(pair)]

        if not planned_match:
            return None
        actual_match = planned_match[0]
        if actual_match.home_pk == pk:
            # Home case
            res = DdOpponentStruct()
            opponent_club: DdClub = self._clubs[actual_match.away_pk]
            res.club_name = opponent_club.name
            res.match_surface = self._clubs[pk].surface
            res.player = opponent_club.selected_player
            return res
        if actual_match.away_pk == pk:
            # Away case
            res = DdOpponentStruct()
            opponent_club = self._clubs[actual_match.home_pk]
            res.club_name = opponent_club.name
            res.match_surface = opponent_club.surface
            res.player = None
            return res
        raise Exception("Bad schedule.")
