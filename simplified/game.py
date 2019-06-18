
"""
Created Apr 09, 2019

@author montreal91
"""

import json

from copy import deepcopy
from random import choice
from random import randint
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

from configuration.config_game import DdGameplayConstants
from simplified.attendance import DdAttendanceParams
from simplified.attendance import DdAttendanceCalculator
from simplified.attendance import DdCourt
from simplified.club import DdClub
from simplified.competition import DdAbstractCompetition
from simplified.financial import DdTransaction
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
    """Passive class to store game parameters."""

    # Various parameters
    attendance_params: DdAttendanceParams
    championship_params: DdChampionshipParams
    playoff_params: DdPlayoffParams

    # Other data
    courts: Dict[str, DdCourt]
    is_hard: bool
    recovery_function: Callable[[DdPlayer], int]
    starting_balance: int
    starting_club: int
    starting_players: int


class DdOpponentStruct:
    """Passive class to store information about opponent for the next match."""
    club_name: str
    match_surface: str
    player: Optional[DdPlayer]


class DdGameDuck:
    """
    A class that incapsulates the game logic.

    Public methods of this class validate user inputs. If input is incorrect,
    an error with (hopefully) descriptive message is raised.
    """

    _SURFACES = (
        DdCourtSurface.CLAY,
        DdCourtSurface.GRASS,
        DdCourtSurface.HARD,
    )

    _attendance_calculator: Callable
    _clubs: Dict[int, DdClub]
    _competition: DdAbstractCompetition
    _history: List[Dict[str, Any]]
    _params: DdGameParams
    _player_factory: DdPlayerFactory
    _season_fame: Dict[int, int]
    _results: List[DdMatchResult]

    def __init__(self, params: DdGameParams):
        self._history = [{}]
        self._params = params
        self._player_factory = DdPlayerFactory()
        self._results = []

        self._attendance_calculator = DdAttendanceCalculator(
            price=self._params.attendance_params.price,
            home_fame=self._params.attendance_params.away_fame,
            away_fame=self._params.attendance_params.away_fame,
            reputation=self._params.attendance_params.reputation,
            importance=self._params.attendance_params.importance,
            hard=self._params.is_hard
        )

        self._clubs = {}
        self._season_fame = {}

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
            balance=self._clubs[self._params.starting_club].account.balance,
            day=self._competition.day,
            clubs=[club.name for club in self._clubs.values()],
            court=self._clubs[self._params.starting_club].court.json,
            history=self._history,
            last_results=self._last_results,
            opponent=self._GetOpponent(self._params.starting_club),
            remaining_matches=self._competition.GetClubSchedule(
                self._params.starting_club
            ),
            standings=self._standings,
            title=self._competition.title,
            users_club=self._params.starting_club,
            user_players=self._user_players,
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

    def ProceedToNextCompetition(self):
        """Updates game while player action is not required."""

        step = True
        while self._competition.day != 0 and step:
            step = self.Update()

    def SelectCoachForPlayer(
        self, coach_index: int, player_index: int, pk: int
    ):
        """
        Selects a coach (bad, normal, or good) for the player in the club.
        """

        assert pk in self._clubs, "Incorrect club pk."
        assert 0 <= player_index < len(self._clubs[pk].players), (
            "Incorrect player index."
        )
        assert 0 <= coach_index < len(DdClub.COACH_LEVELS), (
            "Incorrect coach index."
        )

        self._clubs[pk].SelectCoach(
            coach_index=coach_index, player_index=player_index
        )

    def SelectCourt(self, pk: int, court: str):
        """Selects court for club from available options."""

        assert pk in self._clubs, "Incorrect club pk."
        possible_courts = "|".join(self._params.courts)
        assert court in self._params.courts, (
            "Incorrect court type.\n"
            f"Possible correct types: {possible_courts}"
        )

        self._clubs[pk].court = deepcopy(self._params.courts[court])

    def SelectPlayer(self, i: int, pk: int):
        """Sets selected player for user."""

        assert 0 <= pk < len(self._clubs), "Incorrect club pk."
        assert 0 <= i < len(self._clubs[pk].players), (
            "Incorrect player index."
        )
        self._clubs[pk].SelectPlayer(i)

    def SetTicketPrice(self, pk: int, price: int):
        """Sets ticket price on club's court."""

        assert pk in self._clubs, "Incorrect club pk."
        assert price >= 0, "Ticket price can't be negative."

        self._clubs[pk].court.ticket_price = price

    def Update(self):
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """

        assert not self._decision_required, (
            "You have to select player for the next match."
        )
        assert self._court_check, (
            "You have insufficient funds to play on this court."
        )

        self._PlayOneDay()
        self._Unselect()

        if self.season_over:
            self._UpdateSeasonFame()
            self._NextSeason()

        if self._competition.is_over:
            self._UpdateSeasonFame()
            self._SaveHistory()
            self._StartPlayoff()
        return True

    @property
    def _court_check(self):
        if self._competition.current_matches is None:
            return True

        def HasHomeMatch(pk):
            for match in self._competition.current_matches:
                if match.home_pk == pk:
                    return True
            return False

        for pk, club in self._clubs.items():
            if not club.is_controlled:
                continue
            if club.court.rent_cost > club.account.balance and HasHomeMatch(pk):
                return False

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
        club = DdClub(
            name=club_name,
            surface=surface,
            court=deepcopy(self._params.courts["default"])
        )
        for i in range(self._params.starting_players):
            age = randint(
                DdGameplayConstants.STARTING_AGE.value,
                DdGameplayConstants.RETIREMENT_AGE.value - 1,
            )

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=age, level=i*2, speciality=choice(self._SURFACES)
            ))

        club.account.ProcessTransaction(DdTransaction(
            self._params.starting_balance,
            "Initial balance",
        ))

        self._clubs[pk] = club
        self._season_fame[pk] = 0

    def _CollectCompetitionFame(self):
        for pk in self._clubs:
            self._season_fame[pk] = self._competition.GetClubFame(pk)

    def _CalculateMatchIncome(self, results: Optional[List[DdMatchResult]]):
        if results is None:
            return

        for result in results:
            home_club: DdClub = self._clubs[result.home_pk]
            attendance = self._attendance_calculator(
                ticket_price=home_club.court.ticket_price,
                home_fame=home_club.fame,
                away_fame=self._clubs[result.away_pk].fame,
                reputation=result.home_player_snapshot["reputation"],
                match_importance=self._competition.match_importance,
            )
            income = home_club.court.GetMatchIncome(attendance=attendance)

            result.income = income
            result.attendance = min(attendance, home_club.court.capacity)

            home_club.account.ProcessTransaction(DdTransaction(
                value=-home_club.court.rent_cost,
                comment="Court rent cost."
            ))

            home_club.account.ProcessTransaction(DdTransaction(
                value=income,
                comment=(
                    f"{self._competition.title}, {self._competition.day}, "
                    f"attendance: {attendance}, "
                    f"ticket price: {home_club.court.ticket_price}."
                ),
            ))

    def _NextSeason(self):
        previous_standings = self._history[-1]["Championship"]
        for i, row in enumerate(previous_standings):
            club: DdClub = self._clubs[row.club_pk]
            coach_index = 1 if i < len(previous_standings) // 2 else 2
            for j, slot in enumerate(club.players):
                slot.player.AgeUp()
                slot.player.AfterSeasonRest()
                if not club.is_controlled:
                    club.SelectCoach(coach_index=coach_index, player_index=j)
            club.AddFame(self._season_fame[row.club_pk])
            self._season_fame[row.club_pk] = 0
            club.ExpelRetiredPlayers()

            if club.is_controlled:
                continue

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=0,
                speciality=club.surface
            ))
            club.SelectCoach(coach_index=coach_index, player_index=-1)

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=0,
                speciality=choice(self._SURFACES),
            ))
            club.SelectCoach(coach_index=coach_index, player_index=-1)

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
            for player_coach in club.players:
                player_coach.player.RecoverStamina(
                    self._params.recovery_function(player_coach.player)
                )

    def _PlayOneDay(self):
        self._results = self._competition.Update()

        self._CalculateMatchIncome(self._results)

        if self._results is None and self._competition.title == "Championship":
            self._PerformPractice()

        self._Recover()

    def _SaveHistory(self):
        self._history[-1][self._competition.title] = self._competition.standings

        # This is done for collecting match statistics.
        with open("simplified/results.csv", "a") as results_file:
            for match in self._competition.results_:
                print(match.csv, file=results_file)

    def _StartPlayoff(self):
        self._competition = DdPlayoff(
            self._clubs,
            self._params.playoff_params,
            self._competition.standings,
        )

    def _Unselect(self):
        for club in self._clubs.values():
            club.SelectPlayer(None)

    def _UpdateSeasonFame(self):
        for pk in self._clubs:
            self._season_fame[pk] += self._competition.GetClubFame(pk)

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
