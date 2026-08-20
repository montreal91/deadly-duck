
"""
The actual game.

AssertionErrors are largely used by this module as a GameLogicExceptions.

Created Apr 09, 2019

@author montreal91
"""
import logging
import time
from random import randint
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Set
from typing import Tuple

from configuration.config_game import DdGameplayConstants
from core.club import Club
from core.club import ClubPlayerSlot
from core.competition import CompetitionType
from core.competition import DdAbstractCompetition
from core.financial import DdPracticeCalculator
from core.financial import DdStaticContractCalculator
from core.financial import DdTransaction
from core.match import DdMatchResult
from core.match import DdScheduledMatchStruct
from core.match import DdStandingsRowStruct
from core.player import ExhaustedLinearRecovery
from core.player import Player
from core.player import PlayerFactory
from core.playoffs import DdPlayoff
from core.playoffs import DdPlayoffParams
from core.regular_championship import ChampionshipParams
from core.regular_championship import RegularChampionship
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_CLUB_ID_ERROR = "Incorrect club id."
_UNCONTRACTED_PLAYERS_ERROR = (
    "Your club has uncontracted players.\n"
    "You should whether contract them or fire."
)


class GameParams(NamedTuple):
    """Passive class to store game parameters."""

    # Various parameters
    championship_params: ChampionshipParams
    playoff_params: DdPlayoffParams

    # Other data
    contracts: List[int]
    exhaustion_factor: int
    is_hard: bool
    training_coefficient: int
    years_to_simulate: int


class OpponentDto:
    """Passive class to store information about opponent for the next match."""
    club_name: str
    player: Optional[Player]
    fame: Optional[int]


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
    filename='app.log',
    filemode='a'
)


class Game:
    """
    A class that encapsulates the game logic.

    Public methods of this class validate user inputs. If input is incorrect,
    an error with (hopefully) descriptive message is raised.
    """

    _game_id: str
    _attendance_calculator: Callable
    _competition: DdAbstractCompetition
    _contract_calculator: Callable[[int], int]
    _free_agents: List[Player]
    _history: List[Dict[CompetitionType, Any]]
    _params: GameParams
    _player_factory: PlayerFactory
    _season_fame: Dict[str, int]
    _results: List[DdMatchResult]
    _practice_calculator: DdPracticeCalculator

    def __init__(
            self,
            params: GameParams,
            game_id: str,
            created_ts: int,
            updated_ts: int,
    ):
        self._game_id = game_id
        self._manager_club_id = None
        self._free_agents = []
        self._history = [{}]
        self._params = params
        self._player_factory = PlayerFactory()
        self._results = []

        self._season_fame = {}
        self._contract_calculator = DdStaticContractCalculator(
            self._params.contracts
        )
        self._practice_calculator = DdPracticeCalculator(
            self._params.training_coefficient
        )

        self._created_ts = created_ts
        self._updated_ts = updated_ts

        tcp = TemporalClubProvider.get_instance()
        clubs = tcp.init_clubs_for_game(self._game_id)

        self._competition = RegularChampionship(
            clubs,
            self._params.championship_params
        )

        self._simulate(self._params.years_to_simulate)
        self._generate_free_agents()

    @property
    def day(self):
        return self._competition.day

    @property
    def competition(self):
        return self._competition

    @property
    def clubs(self):
        return self._competition._clubs

    @property
    def game_id(self) -> str:
        return self._game_id

    @property
    def manager_club_id(self):
        return self._manager_club_id

    @property
    def is_over(self) -> bool:
        """Indicates if game is over."""

        return False  # The game never ends yet :)

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        return isinstance(self._competition, DdPlayoff) and self._competition.is_over

    @property
    def created_ts(self):
        return self._created_ts

    @property
    def updated_ts(self):
        return self._updated_ts

    # TODO: Get rid of this hack
    @property
    def _clubs(self):
        return self._competition._clubs

    def rebind_clubs_to_provider(self):
        provider = TemporalClubProvider.get_instance()
        clubs = provider.get_clubs_for_game(self._game_id)

        if not clubs:
            clubs = self._competition._clubs

        self._competition._clubs = clubs

    def fire_player(self, player_id: str, club_id: str):
        """Fires the selected player from user's club."""

        assert club_id in self._clubs, _CLUB_ID_ERROR

        assert self._clubs[club_id].has_player(player_id), (
            "There is no player with such index in your club."
        )

        player = self._clubs[club_id].pop_player(player_id)
        player.has_next_contract = False
        player.RecoverStamina(player.max_stamina)

        self._free_agents.append(player)

    def get_context(self, pk: str) -> Dict[str, Any]:
        """A dictionary with information available for user."""

        assert pk in self._clubs, _CLUB_ID_ERROR

        # TODO: Replace this dict with a NamedTuple class
        return dict(
            balance=self._clubs[pk].account.balance,
            club_name=self._clubs[pk].name,
            day=self._competition.day,
            clubs=[club.name for club in self._clubs.values()],
            free_agents=self._get_free_agents(),
            history=self._history,
            last_results=self._last_results,
            opponent=self._get_opponent(pk),
            practice_cost=self._calculate_club_practice_cost(club=self._clubs[pk]),
            remaining_matches=self._competition.get_club_schedule(pk),
            standings=self._standings,
            title=self._competition.title,
            user_players=self._get_user_players(pk),
            competition=self._competition.title,
            competition_type=self._competition_type,
            has_matches=self._has_matches(),
        )

    def hire_free_agent(self, club_pk: str, player_pk: int):
        """Hires a free agent for the given club."""

        assert player_pk in range(len(self._free_agents)), (
            "There is no free agent with such pk."
        )

        player = self._free_agents[player_pk]
        self._process_player_hire(club_pk=club_pk, player=player)
        self._free_agents.pop(player_pk)

    def hire_new_player(self, club_id: str):
        """Hires a new player for the given club."""

        player = self._player_factory.create_player(
            level=0,
            age=DdGameplayConstants.STARTING_AGE.value,
        )
        self._process_player_hire(club_pk=club_id, player=player)

    def proceed_to_next_competition(self):
        """Updates game while player action is not required."""

        step = True
        while self._competition.day != 0 and step:
            step = self.update()

    def select_coach_for_player(
        self, coach_index: int, player_id: str, club_index: str
    ):
        """
        Selects a coach (bad, normal, or good) for the player in the club.
        """

        assert club_index in self._clubs, _CLUB_ID_ERROR
        assert self._clubs[club_index].has_player(player_id), (
            "Incorrect player index."
        )
        assert 0 <= coach_index < len(Club.COACH_LEVELS), (
            "Incorrect coach index."
        )

        self._clubs[club_index].select_coach(
            coach_index=coach_index, player_id=player_id
        )

    def select_player(self, player_id: str, club_id: str):
        """Sets selected player for user."""

        assert club_id in self._clubs, _CLUB_ID_ERROR
        assert self._clubs[club_id].has_player(player_id), (
            "Incorrect player index."
        )
        self._clubs[club_id].select_player(player_id)

    def set_managed(self, club_id, is_controlled):
        """Sets flag whether club is controlled by a user or not."""

        assert club_id in self._clubs, _CLUB_ID_ERROR
        self._manager_club_id = club_id
        self._clubs[club_id].set_controlled(is_controlled)

    def sign_player(self, club_id: str, player_id: str):
        """Signs a new contract with a player for the next season."""

        if club_id not in self._clubs:
            return False, _CLUB_ID_ERROR

        club = self._clubs[club_id]
        player_slot = club.get_player_slot(player_id)

        if player_slot is None:
            return False, "Incorrect player id."

        if player_slot.has_next_contract:
            return False, "This player already has a contract for the next season."

        next_age = player_slot.player.age + 1
        if next_age >= DdGameplayConstants.RETIREMENT_AGE.value:
            return False, f"{player_slot.player.initials} is too old to play next season."

        cost = self._contract_calculator(player_slot.player.level)

        if self._clubs[club_id].account.balance < cost:
            return False, f"Insufficient funds.\nYou need at least ${cost}."

        club.contract_player(player_id)
        club.account.ProcessTransaction(DdTransaction(
            -cost,
            f"Renewed player contract with {player_slot.player.initials} "
        ))

        return True, "Ok"

    def update(self):
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """

        for club_pk in self._clubs:
            if not self._is_club_valid(club_pk):
                self._clubs[club_pk].set_controlled(False)

        if self.is_over:
            return False, "The game is over"

        if self.season_over and not self._contract_check:
            return False, _UNCONTRACTED_PLAYERS_ERROR

        if self._decision_required:
            return False, "You have to select player for the next match."

        if not self._training_check:
            return False, "You have insufficient funds to perform such kind of training."

        self._perform_practice()
        self._play_one_day()
        self._unselect()

        if self.season_over:
            self._update_season_fame()
            self._save_competition_results()
            self._next_season()
            self._drop_stats()

        if self._competition.is_over:
            self._update_season_fame()
            self._save_competition_results()
            self._start_playoff()

        self._updated_ts = time.time_ns() // 1_000_000

        return True, "Ok"

    @property
    def _can_practice(self) -> bool:
        if self._competition.current_matches is not None:
            return False
        return self._competition_type == CompetitionType.CHAMPIONSHIP

    @property
    def _contract_check(self) -> bool:
        def check_club(c: Club) -> bool:
            for slot in c.players:
                next_age = slot.player.age + 1
                if next_age >= DdGameplayConstants.RETIREMENT_AGE.value:
                    continue
                if not slot.has_next_contract:
                    return False
            return True

        for club in self._clubs.values():
            if not self._is_manager_club(club.club_id):
                continue
            if not check_club(club):
                return False

        return True

    @property
    def _decision_required(self) -> bool:
        if self._competition.current_matches is None:
            return False
        for match in self._competition.current_matches:
            if self._manager_club_id not in (match.home_pk, match.away_pk):
                continue
            if not self._clubs[self._manager_club_id].has_selected_player:
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
        return [DdStandingsRowStruct(i) for i in self._clubs]

    @property
    def _competition_type(self) -> CompetitionType:
        if isinstance(self._competition, RegularChampionship):
            return CompetitionType.CHAMPIONSHIP
        if isinstance(self._competition, DdPlayoff):
            return CompetitionType.PLAY_OFFS
        raise Exception("Unknown competition type.")

    @property
    def _training_check(self) -> bool:
        if self._competition.current_matches is not None:
            return True
        if self._competition.title != "Championship":
            return True

        def check_club(c: Club) -> bool:
            return self._calculate_club_practice_cost(c) <= c.account.balance

        for club in self._clubs.values():
            if not self._is_manager_club(club.club_id):
                continue
            if not check_club(club):
                return False
        return True

    def _has_matches(self):
        matches = self._competition.current_matches

        if matches is None:
            return False

        return len(matches) > 0

    def _calculate_club_practice_cost(self, club: Club) -> int:
        slots = [(s.player.level, s.coach_level) for s in club.players]
        return sum(self._practice_calculator(*slot) for slot in slots)

    def _calculate_match_income(self):
        for club in self._clubs.values():
            club.account.ProcessTransaction(DdTransaction(
                value=250_000,
                comment="Income"
            ))

    def _collect_competition_fame(self):
        for pk in self._clubs:
            self._season_fame[pk] = self._competition.get_club_fame(pk)

    def _drop_stats(self):
        for club in self._clubs.values():
            for data in club.players:
                data.player.DropStats()

    def _generate_free_agents(self):
        new_agents = []
        for _ in range(randint(3, 10)):
            new_agents.append(self._player_factory.create_player(
                age=randint(
                    DdGameplayConstants.STARTING_AGE.value,
                    DdGameplayConstants.RETIREMENT_AGE.value - 1
                ),
                level=randint(1, 10),
            ))
        new_agents.sort(
            key=lambda x: x.level,
            reverse=True,
        )
        self._free_agents = new_agents

    def _get_free_agents(self) -> List[Tuple[Player, int]]:
        res = []
        for agent in self._free_agents:
            res.append((agent, self._contract_calculator(agent.level),))
        return res

    def _get_opponent(self, pk: str) -> Optional[OpponentDto]:
        def schedule_filter(pair: DdScheduledMatchStruct):
            if pair.home_pk == pk:
                return True
            return pair.away_pk == pk

        if self._competition.is_over:
            return None

        schedule = self._competition.current_matches

        # Just in case
        if schedule is None:
            return None
        planned_match = [pair for pair in schedule if schedule_filter(pair)]

        if not planned_match:
            return None
        actual_match = planned_match[0]
        if actual_match.home_pk == pk:
            # Home case
            res = OpponentDto()
            opponent_club: Club = self._clubs[actual_match.away_pk]
            res.club_name = opponent_club.name
            res.player = opponent_club.selected_player
            res.fame = opponent_club.fame
            return res
        if actual_match.away_pk == pk:
            # Away case
            res = OpponentDto()
            opponent_club = self._clubs[actual_match.home_pk]
            res.club_name = opponent_club.name
            res.player = None
            res.fame = None
            return res
        raise Exception("Bad schedule.")

    def _get_user_players(self, pk: str):
        def set_contract_prices(slot: ClubPlayerSlot) -> ClubPlayerSlot:
            slot.contract_cost = self._contract_calculator(slot.player.level)
            return slot

        return [set_contract_prices(slot) for slot in self._clubs[pk].players]

    def _hire_players_if_needed(self):
        for club in self._clubs.values():
            if self._is_manager_club(club.club_id):
                continue
            techs = [slot.player.actual_technique < 5 for slot in club.players]
            if all(techs):
                new_player = self._player_factory.create_player(
                    level=0,
                    age=DdGameplayConstants.STARTING_AGE.value,
                )
                club.add_player(new_player)

    def _is_club_valid(self, pk: str) -> bool:
        opponent = self._get_opponent(pk)
        club: Club = self._clubs[pk]
        if opponent is None or not self._is_manager_club(pk):
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

        return True

    def _next_season(self):
        previous_standings = self._history[-1][CompetitionType.CHAMPIONSHIP]
        for row in previous_standings:
            club: Club = self._clubs[row.club_id]
            for slot in club.players:
                slot.player.AgeUp()
                slot.player.AfterSeasonRest()
                slot.has_next_contract = False
            # TODO: Fix fame calculation
            # club.add_fame(self._season_fame[row.club_id])
            self._season_fame[row.club_id] = 0
            club.expel_retired_players()

            if self._is_manager_club(club.club_id):
                continue

            club.add_player(self._player_factory.create_player(
                age=DdGameplayConstants.STARTING_AGE.value,
                level=randint(5, 10),
            ))

        self._generate_free_agents()

        self._shuffle_coach_powers()
        self._competition = RegularChampionship(
            self._clubs,
            self._params.championship_params
        )
        self._history.append({})

    def _perform_practice(self):
        if not self._can_practice:
            return

        for club in self._clubs.values():
            if self._is_manager_club(club.club_id):
                club.account.ProcessTransaction(DdTransaction(
                    -self._calculate_club_practice_cost(club),
                    f"Practice on day {self._competition.day}"
                ))
            club.perform_practice()

    def _play_one_day(self):
        current_matches = self._competition.current_matches
        playing_player_ids = self._get_playing_player_ids(current_matches)

        self._results = self._competition.update()
        self._calculate_match_income()

        self._recover(excluded_player_ids=playing_player_ids)

        self._hire_players_if_needed()

    def _process_player_hire(self, club_pk: str, player: Player):
        assert club_pk in self._clubs, _CLUB_ID_ERROR

        cost = self._contract_calculator(player.level)

        assert self._clubs[club_pk].account.balance >= cost, (
            "Insufficient funds.\n"
            f"You need at least ${cost}."
        )
        self._clubs[club_pk].add_player(player)
        if self._is_manager_club(club_pk):
            self._clubs[club_pk].select_coach(
                coach_index=0,
                player_id=player.player_id,
            )
        self._clubs[club_pk].account.ProcessTransaction(DdTransaction(
            -cost,
            f"New player contract with {player.initials}."
        ))

    def _recover(self, excluded_player_ids: Set[str]):
        recovery_function = ExhaustedLinearRecovery(
            self._params.exhaustion_factor
        )
        for club in self._clubs.values():
            for slot in club.players:
                if slot.player.player_id in excluded_player_ids:
                    continue
                slot.player.RecoverStamina(
                    recovery_function(slot.player)
                )

    def _get_playing_player_ids(self, matches) -> Set[str]:
        if matches is None:
            return set()

        player_ids = set()
        for match in matches:
            for club_id in (match.home_pk, match.away_pk):
                player = self._clubs[club_id].selected_player
                if player is not None:
                    player_ids.add(player.player_id)

        return player_ids

    def _is_manager_club(self, club_id: str) -> bool:
        return self._manager_club_id == club_id

    def _simulate(self, years):
        while len(self._history) < years:
            self.update()

    def _save_competition_results(self):
        self._history[-1][self._competition_type] = self._competition.standings

    def _start_playoff(self):
        self._competition = DdPlayoff(
            self._clubs,
            self._params.playoff_params,
            self._competition.standings,
        )

    def _unselect(self):
        for club in self._clubs.values():
            club.select_player(None)

    def _update_season_fame(self):
        # TODO: Fix fame calculation
        pass

    # This whole method is a temporary hack before I'll implement a proper AI
    def _shuffle_coach_powers(self):
        from random import shuffle
        strong_clubs = [pk for pk, club in self._clubs.items() if club.coach_power == 3 and not self._is_manager_club(pk)]
        medium_clubs = [pk for pk, club in self._clubs.items() if club.coach_power == 2 and not self._is_manager_club(pk)]
        weaksy_clubs = [pk for pk, club in self._clubs.items() if club.coach_power == 1 and not self._is_manager_club(pk)]

        shuffle(strong_clubs)
        shuffle(medium_clubs)
        shuffle(weaksy_clubs)

        while len(strong_clubs) > 5:
            medium_clubs.append(strong_clubs.pop())

        while len(medium_clubs) > 6:
            weaksy_clubs.append(medium_clubs.pop())


        s, m, w = strong_clubs.pop(), medium_clubs.pop(), weaksy_clubs.pop()
        s, m, w = m, w, s  # cycle

        logging.debug(f"Strong club going weak:   {self._clubs[s].name}")
        logging.debug(f"Medium club going strong: {self._clubs[m].name}")
        logging.debug(f"Weak club going medium:   {self._clubs[w].name}")

        strong_clubs.append(s)
        medium_clubs.append(m)
        weaksy_clubs.append(w)

        [self._clubs[pk].set_coach_power(3) for pk in strong_clubs]
        [self._clubs[pk].set_coach_power(2) for pk in medium_clubs]
        [self._clubs[pk].set_coach_power(1) for pk in weaksy_clubs]
