
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
from typing import Tuple

from configuration.config_game import DdGameplayConstants
from core.attendance import DdAttendanceParams
from core.attendance import DdAttendanceCalculator
from core.attendance import DdCourt
from core.club import DdClub
from core.club import DdClubPlayerSlot
from core.competition import DdAbstractCompetition
from core.financial import DdPracticeCalculator
from core.financial import DdStaticContractCalculator
from core.financial import DdTransaction
from core.match import DdMatchResult
from core.match import DdScheduledMatchStruct
from core.match import DdStandingsRowStruct
from core.player import DdCourtSurface
from core.player import DdExhaustedLinearRecovery
from core.player import DdPlayer
from core.player import DdPlayerFactory
from core.playoffs import DdPlayoff
from core.playoffs import DdPlayoffParams
from core.regular_championship import DdChampionshipParams
from core.regular_championship import DdRegularChampionship
from core.serialization import DdJsonDecoder


_CLUB_INDEX_ERROR = "Incorrect club index."


class DdGameParams(NamedTuple):
    """Passive class to store game parameters."""

    # Various parameters
    attendance_params: DdAttendanceParams
    championship_params: DdChampionshipParams
    playoff_params: DdPlayoffParams

    # Other data
    contracts: List[int]
    courts: Dict[str, DdCourt]
    exhaustion_factor: int
    is_hard: bool
    training_coefficient: int
    years_to_simulate: int


class DdOpponentStruct:
    """Passive class to store information about opponent for the next match."""
    club_name: str
    match_surface: str
    player: Optional[DdPlayer]
    fame: Optional[int]


class Game:
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
    _contract_calculator: Callable[[int], int]
    _free_agents: List[DdPlayer]
    _history: List[Dict[str, Any]]
    _params: DdGameParams
    _player_factory: DdPlayerFactory
    _season_fame: Dict[int, int]
    _results: List[DdMatchResult]
    _practice_calculator: DdPracticeCalculator

    def __init__(self, params: DdGameParams, game_id: str, manager_club_id: int):
        self._game_id = game_id
        self._manager_club_id = manager_club_id
        self._free_agents = []
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
        self._contract_calculator = DdStaticContractCalculator(
            self._params.contracts
        )
        self._practice_calculator = DdPracticeCalculator(
            self._params.training_coefficient
        )

        decoder = DdJsonDecoder()
        decoder.Register(DdPlayer)
        decoder.Register(DdClubPlayerSlot)
        with open("configuration/clubs.json", "r") as data_file:
            club_data = json.load(data_file, object_hook=decoder)

        for pk, club in enumerate(club_data):
            self._AddClub(pk=pk, club_data=club)

        self._competition = DdRegularChampionship(
            self._clubs, self._params.championship_params
        )

        self._Simulate(self._params.years_to_simulate)
        self._GenerateFreeAgents()

    @property
    def day(self):
        return self._competition.day

    @property
    def game_id(self):
        return self._game_id

    @property
    def manager_club_id(self):
        return self._manager_club_id

    @property
    def is_over(self) -> bool:
        """Indicates if game is over."""

        return False  # The game never ends yet :)
        # return not any(club.is_controlled for club in self._clubs.values())

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        return self._competition.title == "Cup" and self._competition.is_over

    def FirePlayer(self, i: int, pk: int):
        """Fires the selected player from user's club."""

        assert 0 <= pk < len(self._clubs), _CLUB_INDEX_ERROR

        assert i >= 0, "Player index should be positive."
        assert i < len(self._clubs[pk].players), (
            "There is no player with such index in your club."
        )

        player = self._clubs[pk].PopPlayer(i)
        player.has_next_contract = False
        player.RecoverStamina(player.max_stamina)

        self._free_agents.append(player)

    def get_context(self, pk: int) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        assert 0 <= pk < len(self._clubs), _CLUB_INDEX_ERROR

        return dict(
            balance=self._clubs[pk].account.balance,
            club_name=self._clubs[pk].name,
            day=self._competition.day,
            clubs=[club.name for club in self._clubs.values()],
            court=self._clubs[pk].court.json,
            free_agents=self._GetFreeAgents(),
            history=self._history,
            last_results=self._last_results,
            opponent=self._GetOpponent(pk),
            practice_cost=self._CalculateClubPracticeCost(club=self._clubs[pk]),
            remaining_matches=self._competition.GetClubSchedule(pk),
            standings=self._standings,
            title=self._competition.title,
            user_players=self._GetUserPlayers(pk),
        )

    def hire_free_agent(self, club_pk: int, player_pk: int):
        """Hires a free agent for the given club."""

        assert player_pk in range(len(self._free_agents)), (
            "There is no free agent with such pk."
        )

        player = self._free_agents[player_pk]
        self._ProcessPlayerHire(club_pk=club_pk, player=player)
        self._free_agents.pop(player_pk)

    def HireNewPlayer(self, surface: str, pk: int):
        """Hires a new player for the given club."""

        choices = "|".join(self._SURFACES)
        assert surface in self._SURFACES, (
            "You can't choose such speciality.\n"
            "Choices are: "
            f"{choices}"
        )
        player = self._player_factory.CreatePlayer(
            level=0,
            age=DdGameplayConstants.STARTING_AGE.value,
            speciality=surface
        )
        self._ProcessPlayerHire(club_pk=pk, player=player)

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

        assert pk in self._clubs, _CLUB_INDEX_ERROR
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

        assert pk in self._clubs, _CLUB_INDEX_ERROR
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

    def _set_controlled(self, pk: int, is_controlled: bool):
        """Sets flag wether club is controlled by a user or not."""

        assert 0 <= pk < len(self._clubs), "Incorrect club pk."
        self._clubs[pk].SetControlled(is_controlled)

    def SetTicketPrice(self, pk: int, price: int):
        """Sets ticket price on club's court."""

        assert pk in self._clubs, _CLUB_INDEX_ERROR
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
        assert not players[i].has_next_contract, (
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

        for club_pk in self._clubs:
            if not self._IsClubValid(club_pk):
                self._clubs[club_pk].SetControlled(False)
        assert not self.is_over, ("The game is over.")

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
            self._DropStats()

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
                if not slot.has_next_contract:
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
            return self._CalculateClubPracticeCost(club) <= club.account.balance

        for club in self._clubs.values():
            if not club.is_controlled:
                continue
            if not CheckClub(club):
                return False
        return True

    def _AddClub(self, pk: int, club_data: Dict[str, Any]):
        club = DdClub(
            name=club_data["name"],
            surface=club_data["surface"],
            coach_power=club_data["coach_power"],
            court=deepcopy(self._params.courts["default"])
        )

        for value in club_data["fame"]:
            club.AddFame(value)

        for i, slot in enumerate(club_data["player_data"]):
            club.AddPlayer(slot.player)
            if slot.has_next_contract:
                club.ContractPlayer(player_pk=i)

        club.account.ProcessTransaction(DdTransaction(
            club_data["balance"],
            "Initial balance",
        ))

        self._clubs[pk] = club
        self._season_fame[pk] = 0

    def _CalculateClubPracticeCost(self, club: DdClub) -> int:
        slots = [(s.player.level, s.coach_level) for s in club.players]
        return sum(self._practice_calculator(*slot) for slot in slots)

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

    def _CheckContracts(self):
        if not self._contract_check:
            raise AssertionError(
                "Your club has uncontracted players.\n"
                "You should wether contract them or fire."
            )

    def _CollectCompetitionFame(self):
        for pk in self._clubs:
            self._season_fame[pk] = self._competition.GetClubFame(pk)

    def _DropStats(self):
        for club in self._clubs.values():
            for data in club.players:
                data.player.DropStats()

    def _GenerateFreeAgents(self):
        new_agents = []
        for _ in range(randint(3, 10)):
            new_agents.append(self._player_factory.CreatePlayer(
                age=randint(
                    DdGameplayConstants.STARTING_AGE.value,
                    DdGameplayConstants.RETIREMENT_AGE.value - 1
                ),
                level=randint(1, 10),
                speciality=choice(self._SURFACES),
            ))
        new_agents.sort(
            key=lambda x: (x.speciality, x.level),
            reverse=True,
        )
        self._free_agents = new_agents

    def _GetFreeAgents(self) -> List[Tuple[DdPlayer, int]]:
        res = []
        for agent in self._free_agents:
            res.append((agent, self._contract_calculator(agent.level),))
        return res

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

    def _GetUserPlayers(self, pk: int) -> List[DdClubPlayerSlot]:

        def SetContractPrices(slot: DdClubPlayerSlot) -> DdClubPlayerSlot:
            slot.contract_cost = self._contract_calculator(slot.player.level)
            return slot

        return [SetContractPrices(slot) for slot in self._clubs[pk].players]

    def _HirePlayersIfNeeded(self):
        for club in self._clubs.values():
            if club.is_controlled:
                continue
            techs = [slot.player.actual_technique < 5 for slot in club.players]
            if all(techs):
                new_player = self._player_factory.CreatePlayer(
                    level=0,
                    age=DdGameplayConstants.STARTING_AGE.value,
                    speciality=club.surface
                )
                club.AddPlayer(new_player)

    def _IsClubValid(self, pk: int) -> bool:
        opponent = self._GetOpponent(pk)
        club: DdClub = self._clubs[pk]
        if opponent is None or not club.is_controlled:
            return True

        best_player = max(
            [slot.player.actual_technique for slot in club.players],
            default=0,
        )

        min_player_contract = self._contract_calculator(level=0)
        if best_player <= 0 and club.account.balance < min_player_contract:
            return False

        if opponent.player is None:
            return True

        if club.account.balance < self._params.courts["default"].rent_cost:
            return False

        return True

    def _LogTrainingCosts(self, club: DdClub):
        with open(".logs/trainings.csv", "a") as log_file:
            cost = self._CalculateClubPracticeCost(club)
            print(
                f"{len(self._history) + 1},{self._competition.day},{cost}",
                file=log_file
            )

    def _NextSeason(self):
        previous_standings = self._history[-1]["Championship"]
        for row in previous_standings:
            club: DdClub = self._clubs[row.club_pk]
            for slot in club.players:
                slot.player.AgeUp()
                slot.player.AfterSeasonRest()
                slot.has_next_contract = False
            club.AddFame(self._season_fame[row.club_pk])
            self._season_fame[row.club_pk] = 0
            club.ExpelRetiredPlayers()

            if club.is_controlled:
                continue

            club.AddPlayer(self._player_factory.CreatePlayer(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=randint(0, 5),
                speciality=club.surface
            ))

        self._GenerateFreeAgents()

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

            if club.is_controlled:
                club.account.ProcessTransaction(DdTransaction(
                    -self._CalculateClubPracticeCost(club),
                    f"Practice on day {self._competition.day}"
                ))
            club.PerformPractice()

    def _PlayOneDay(self):
        self._results = self._competition.Update()
        self._CalculateMatchIncome(self._results)
        self._Recover()
        self._HirePlayersIfNeeded()

    def _ProcessPlayerHire(self, club_pk: int, player: DdPlayer):
        assert club_pk in self._clubs, _CLUB_INDEX_ERROR

        cost = self._contract_calculator(player.level)

        assert self._clubs[club_pk].account.balance >= cost, (
            "Insufficient funds.\n"
            f"You need at least ${cost}."
        )
        self._clubs[club_pk].AddPlayer(player)
        self._clubs[club_pk].account.ProcessTransaction(DdTransaction(
            -cost,
            f"New player contract with {player.initials} "
            f"speciality {player.speciality}."
        ))

    def _Recover(self):
        recovery_function = DdExhaustedLinearRecovery(
            self._params.exhaustion_factor
        )
        for club in self._clubs.values():
            for slot in club.players:
                slot.player.RecoverStamina(
                    recovery_function(slot.player)
                )

    def _SaveHistory(self):
        self._history[-1][self._competition.title] = self._competition.standings

        # This is done for collecting match statistics.
        with open(".logs/results.csv", "a") as results_file:
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
