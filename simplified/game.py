
"""
The actual game.

AssertionErrors are largely used by this module as a GameLogicExceptions.

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
from simplified.club import DdClubPlayerSlot
from simplified.competition import DdAbstractCompetition
from simplified.financial import DdContractCalculator
from simplified.financial import DdTrainingCalculator
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
from simplified.serialization import DdJsonDecoder


class DdGameParams(NamedTuple):
    """Passive class to store game parameters."""

    # Various parameters
    attendance_params: DdAttendanceParams
    championship_params: DdChampionshipParams
    playoff_params: DdPlayoffParams

    # Other data
    contract_coefficient: int
    courts: Dict[str, DdCourt]
    is_hard: bool
    recovery_function: Callable[[DdPlayer], int]
    starting_balance: int
    starting_club: int
    starting_players: int
    training_coefficient: int
    years_to_simulate: int


class DdOpponentStruct:
    """Passive class to store information about opponent for the next match."""
    club_name: str
    match_surface: str
    player: Optional[DdPlayer]
    fame: Optional[int]


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
    _contract_calculator: DdContractCalculator
    _history: List[Dict[str, Any]]
    _params: DdGameParams
    _player_factory: DdPlayerFactory
    _season_fame: Dict[int, int]
    _results: List[DdMatchResult]
    _training_calculator: DdTrainingCalculator

    def __init__(self, params: DdGameParams):
        self._history = [{}]
        self._params = params
        self._player_factory = DdPlayerFactory()
        self._results = []

        self._attendance_calculator = DdAttendanceCalculator(
            price=self._params.attendance_params.price,
            home_fame=self._params.attendance_params.home_fame,
            away_fame=self._params.attendance_params.away_fame,
            reputation=self._params.attendance_params.reputation,
            importance=self._params.attendance_params.importance,
            hard=self._params.is_hard
        )

        self._clubs = {}
        self._season_fame = {}
        self._contract_calculator = DdContractCalculator(
            self._params.contract_coefficient
        )
        self._training_calculator = DdTrainingCalculator(
            self._params.training_coefficient
        )

        decoder = DdJsonDecoder()
        decoder.Register(DdPlayer)
        with open("configuration/clubs.json", "r") as data_file:
            club_data = json.load(data_file, object_hook=decoder)

        for pk, club in enumerate(club_data):
            self._AddClub(pk=pk, club_data=club)

        self._competition = DdRegularChampionship(
            self._clubs, self._params.championship_params
        )

        self._Simulate(self._params.years_to_simulate)
        self._clubs[self._params.starting_club].SetControlled(True)

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

        cost = self._contract_calculator(0)
        choices = "|".join(self._SURFACES)
        assert surface in self._SURFACES, (
            "You can't choose such speciality.\n"
            "Choices are: "
            f"{choices}"
        )
        assert self._clubs[pk].account.balance >= cost, (
            "Insufficient funds.\n"
            f"You need at least ${cost}."
        )

        player = self._player_factory.CreatePlayer(
            level=0,
            age=DdGameplayConstants.STARTING_AGE.value,
            speciality=surface
        )
        self._clubs[pk].AddPlayer(player)
        self._clubs[pk].account.ProcessTransaction(DdTransaction(
            -cost,
            f"New player contract with {player.initials} "
            f"speciality {player.speciality}."
        ))

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

    def SignPlayer(self, pk: int, i: int):
        """Signs a new contract with a player for the next season."""

        assert 0 <= pk < len(self._clubs), "Incorrect club pk."

        club = self._clubs[pk]
        players = self._clubs[pk].players
        assert 0 <= i < len(players), (
            "Incorrect player index."
        )
        assert not players[i].player.has_next_contract, (
            "This player already has a contract for the next season."
        )
        assert (
            players[i].player.age + 1 < DdGameplayConstants.RETIREMENT_AGE.value
        ), (
            f"{players[i].player.initials} is too old to play next season."
        )

        cost = self._contract_calculator(players[i].player.level)
        assert self._clubs[pk].account.balance >= cost, (
            "Insufficient funds.\n"
            f"You need at least ${cost}."
        )

        club.ContractPlayer(i)
        club.account.ProcessTransaction(DdTransaction(
            -cost,
            f"Renewed player contract with {players[i].player.initials} "
        ))

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
        assert self._training_check, (
            "You have insufficient funds to perform such kind of training."
        )

        self._PerformPractice()
        self._PlayOneDay()
        self._Unselect()

        if self.season_over:
            self._CheckContracts()
            self._UpdateSeasonFame()
            self._NextSeason()

        if self._competition.is_over:
            self._UpdateSeasonFame()
            self._SaveHistory()
            self._StartPlayoff()
        return True

    @property
    def _can_practice(self) -> bool:
        if self._competition.current_matches is not None:
            return False
        return self._competition.title == "Championship"

    @property
    def _contract_check(self) -> bool:
        def CheckClub(club: DdClub) -> bool:
            for slot in club.players:
                next_age = slot.player.age + 1
                if next_age >= DdGameplayConstants.RETIREMENT_AGE.value:
                    continue
                if not slot.player.has_next_contract:
                    return False
            return True

        for club in self._clubs.values():
            if not club.is_controlled:
                continue
            if not CheckClub(club):
                return False

        return True

    @property
    def _court_check(self) -> bool:
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
    def _training_check(self) -> bool:
        if self._competition.current_matches is not None:
            return True
        if self._competition.title != "Championship":
            return True

        def CheckClub(club: DdClub) -> bool:
            return self._CalculateClubTrainingCost(club) <= club.account.balance

        for club in self._clubs.values():
            if not club.is_controlled:
                continue
            if not CheckClub(club):
                return False
        return True

    @property
    def _user_players(self) -> List[DdPlayer]:
        def SetContractPrices(slot: DdClubPlayerSlot):
            slot.contract_cost = self._contract_calculator(slot.player.level)
            return slot

        for club in self._clubs.values():
            if club.is_controlled:
                return [SetContractPrices(slot) for slot in club.players]
        return []

    def _AddClub(self, pk: int, club_data: Dict[str, Any]):
        club = DdClub(
            name=club_data["name"],
            surface=club_data["surface"],
            court=deepcopy(self._params.courts["default"])
        )

        for value in club_data["fame"]:
            club.AddFame(value)

        for player in club_data["players"]:
            club.AddPlayer(player)

        club.account.ProcessTransaction(DdTransaction(
            club_data["balance"],
            "Initial balance",
        ))

        self._clubs[pk] = club
        self._season_fame[pk] = 0

    def _CalculateClubTrainingCost(self, club: DdClub) -> int:
        slots = [(s.player.level, s.coach_level) for s in club.players]
        return sum(self._training_calculator(*slot) for slot in slots)

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

    def _CollectCompetitionFame(self):
        for pk in self._clubs:
            self._season_fame[pk] = self._competition.GetClubFame(pk)

    def _CheckContracts(self):
        if not self._contract_check:
            raise AssertionError(
                "Your club has uncontracted players.\n"
                "You should wether contract them or fire."
            )

    def _GetOpponent(self, pk: int) -> Optional[DdOpponentStruct]:
        def ScheduleFilter(pair: DdScheduledMatchStruct):
            if pair.home_pk == pk:
                return True
            return pair.away_pk == pk

        if self._competition.is_over:
            return None

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
            res.fame = opponent_club.fame
            return res
        if actual_match.away_pk == pk:
            # Away case
            res = DdOpponentStruct()
            opponent_club = self._clubs[actual_match.home_pk]
            res.club_name = opponent_club.name
            res.match_surface = opponent_club.surface
            res.player = None
            res.fame = None
            return res
        raise Exception("Bad schedule.")

    def _LogTrainingCosts(self, club: DdClub):
        with open("simplified/.logs/trainings.csv", "a") as log_file:
            cost = self._CalculateClubTrainingCost(club)
            print(
                f"{len(self._history) + 1},{self._competition.day},{cost}",
                file=log_file
            )

    def _NextSeason(self):
        previous_standings = self._history[-1]["Championship"]
        for i, row in enumerate(previous_standings):
            club: DdClub = self._clubs[row.club_pk]
            coach_index = 1 if i < len(previous_standings) // 2 else 2
            for j, slot in enumerate(club.players):
                slot.player.AgeUp()
                slot.player.AfterSeasonRest()
                slot.player.has_next_contract = False
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
        if not self._can_practice:
            return

        for club in self._clubs.values():
            # This cruft is for debugging/balance adjusting reasons.
            if club.is_controlled:
                self._LogTrainingCosts(club)

            club.PerformPractice()
            if club.is_controlled:
                club.account.ProcessTransaction(DdTransaction(
                    -self._CalculateClubTrainingCost(club),
                    f"Training on day {self._competition.day}"
                ))

    def _PlayOneDay(self):
        self._results = self._competition.Update()
        self._CalculateMatchIncome(self._results)
        self._Recover()

    def _Recover(self):
        for club in self._clubs.values():
            for player_coach in club.players:
                player_coach.player.RecoverStamina(
                    self._params.recovery_function(player_coach.player)
                )

    def _SaveHistory(self):
        self._history[-1][self._competition.title] = self._competition.standings

        # This is done for collecting match statistics.
        with open("simplified/.logs/results.csv", "a") as results_file:
            for match in self._competition.results_:
                print(match.csv, file=results_file)

    def _Simulate(self, years):
        while len(self._history) < years:
            self.Update()

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
