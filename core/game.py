"""
The actual game.

AssertionErrors are largely used by this module as a GameLogicExceptions.

Created Apr 09, 2019

@author montreal91
"""
import logging
import time
from datetime import date
from datetime import timedelta
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Set

from configuration.config_game import GameplayConstants
from core.club import Club
from core.club import ClubPlayerSlot
from core.competition import AbstractCompetition
from core.competition import CompetitionType
from core.contract import Contract
from core.financial import DdPracticeCalculator
from core.financial import DdStaticContractCalculator
from core.financial import DdTransaction
from core.match_processing_system import process_matches
from core.match_result import MatchResult
from core.player import ExhaustedLinearRecovery
from core.player import Player
from core.player import PlayerFactory
from core.playoffs import Playoff
from core.playoffs import PlayoffParams
from core.playoffs import PlayoffSeed
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.regular_championship import ChampionshipParams
from core.regular_championship import DdStandingsRowStruct
from core.regular_championship import RegularChampionship
from core.scheduled_match import ScheduledMatch
from core.skill_upgrade_system import upgrade_skills
from core.update_result import UpdateResult

_CLUB_ID_ERROR = "Incorrect club id."
_UNCONTRACTED_PLAYERS_ERROR = (
    "Your club has uncontracted players.\n"
    "You should whether contract them or fire."
)
_FIRST_SEASON_START_DATE = date(2082, 2, 21)
_SEASON_START_MONTH = 2
_SEASON_START_DAY = 21
_MASTER_LEAGUE_ID = "master_league"
_APPRENTICE_LEAGUE_ID = "apprentice_league"
_COMPETITION_LEAGUE_IDS = frozenset({
    _MASTER_LEAGUE_ID,
    _APPRENTICE_LEAGUE_ID,
})


class GameParams(NamedTuple):
    """Passive class to store game parameters."""

    # Various parameters
    championship_params: ChampionshipParams
    playoff_params: PlayoffParams

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
    _contract_calculator: Callable[[int], int]
    _current_date: date
    _free_agents: List[Player]
    _params: GameParams
    _player_factory: PlayerFactory
    _season_fame: Dict[str, int]
    _results: List[MatchResult]
    _practice_calculator: DdPracticeCalculator
    _season_index: int

    def __init__(
            self,
            params: GameParams,
            game_id: str,
            created_ts: int,
            updated_ts: int,
    ):
        self._game_id = game_id
        self._manager_club_id = None
        self._current_date = _FIRST_SEASON_START_DATE
        self._free_agents = []
        self._history = [{}]
        self._params = params
        self._player_factory = PlayerFactory()
        self._results = []
        # self._new_contracts = []

        self._season_fame = {}
        self._contract_calculator = DdStaticContractCalculator(
            self._params.contracts
        )
        self._practice_calculator = DdPracticeCalculator(
            self._params.training_coefficient
        )

        self._created_ts = created_ts
        self._updated_ts = updated_ts
        self._season_index = 0

        self._start_regular_championship(self._clubs)

    @property
    def day(self):
        return self._current_date

    @property
    def current_date(self):
        return self._current_date

    @property
    def cmp(self) -> Optional[AbstractCompetition]:
        repo = CompetitionRepository.tmp_get_instance()
        comps = repo.get_ongoing_competitions(self._game_id)

        if not comps:
            return None

        return comps[0]

    @property
    def clubs(self):
        return self._clubs

    @property
    def game_id(self) -> str:
        return self._game_id

    @property
    def manager_club_id(self):
        return self._manager_club_id

    @property
    def season_index(self) -> int:
        return self._season_index

    @property
    def is_over(self) -> bool:
        """Indicates if game is over."""

        return False  # The game never ends yet :)

    @property
    def season_over(self) -> bool:
        """Checks if season is over."""

        repo = CompetitionRepository.tmp_get_instance()
        competitions = repo.get_season_competitions(
            self._game_id,
            self._season_index,
        )
        playoffs = [
            competition
            for competition in competitions
            if isinstance(competition, Playoff)
        ]
        return any(playoff.is_over for playoff in playoffs)

    @property
    def created_ts(self):
        return self._created_ts

    @property
    def updated_ts(self):
        return self._updated_ts

    def tmp_init(self):
        self._start_regular_championship(self._clubs)

    def get_context(self, pk: str) -> Dict[str, Any]:
        """A dictionary with information available for user."""
        clubs = self._clubs

        assert pk in clubs, _CLUB_ID_ERROR

        cmp = self.cmp

        # TODO: get rid of this shite.
        return dict(
            balance=clubs[pk].account.balance,
            club_name=clubs[pk].name,
            day=self._formatted_current_date,
            opponent=self._get_opponent(cmp, pk),
            practice_cost=self._calculate_club_practice_cost(club=clubs[pk]),
            remaining_matches=_get_remaining_matches(cmp, pk),
            title=_get_competition_title(cmp),
            user_players=self._get_user_players(pk),
            competition=_get_competition_title(cmp),
            competition_type=_get_competition_type(cmp=cmp),
            has_matches=_has_matches(cmp=cmp),
        )

    def proceed_to_next_competition(self):
        """Updates game while player action is not required."""

    def set_managed(self, club_id, is_controlled):
        """Sets flag whether club is controlled by a user or not."""

        assert club_id in self._clubs, _CLUB_ID_ERROR
        self._manager_club_id = club_id
        self._clubs[club_id].set_controlled(is_controlled)

    def update(self, clubs: Dict[str, Club]) -> UpdateResult:
        """
        Updates game state.

        Proceeds to the next day if possible.
        All scheduled matches are performed.
        """
        repo = CompetitionRepository.tmp_get_instance()
        cmps = repo.get_ongoing_competitions(self._game_id)
        if len(cmps) == 0:
            cmp = None
        else:
            cmp = cmps[0]

        for club_pk in clubs:
            if not self._is_club_valid(club_pk, clubs[club_pk], cmp):
                clubs[club_pk].set_controlled(False)

        if self.is_over:
            return UpdateResult(False, "The game is over")

        if self.season_over and not self._contract_check:
            return UpdateResult(False, _UNCONTRACTED_PLAYERS_ERROR)

        if cmp is not None and self._decision_required(cmp, clubs):
            return UpdateResult(False, "You have to select player for the next match.")

        if not self._training_check:
            return UpdateResult(False, "You have insufficient funds to perform such kind of training.")

        new_contracts = self._hire_players_if_needed(clubs)
        self._assign_players(clubs)
        self._perform_practice(clubs)
        self._play_one_day(clubs)

        upgrade_skills(
            clubs=clubs,
            manager_club_id=self._manager_club_id,
        )

        _unselect(clubs)

        if self.season_over:
            self._next_season(clubs)
        elif self._is_regular_season_over():
            self._update_season_fame()
            self._save_competition_results()
            self._start_playoff()

        self._advance_current_date()
        self._updated_ts = time.time_ns() // 1_000_000

        return UpdateResult(True, "Ok", new_contracts)

    def _is_regular_season_over(self) -> bool:
        repo = CompetitionRepository.tmp_get_instance()
        competitions = repo.get_season_competitions(
            self._game_id,
            self._season_index,
        )
        regulars = [cmp for cmp in competitions if isinstance(cmp, RegularChampionship)]
        playoffs = [cmp for cmp in competitions if isinstance(cmp, Playoff)]

        return bool(regulars) and not playoffs and all(
            regular.is_over
            for regular in regulars
        )

    @property
    def _can_practice(self) -> bool:
        cmp = self.cmp
        if cmp is None or cmp.current_matches:
            return False

        return _get_competition_type(cmp) == CompetitionType.CHAMPIONSHIP

    @property
    def _contract_check(self) -> bool:
        def check_club(c: Club) -> bool:
            for slot in c.players:
                if slot.player is None:
                    continue
                next_age = slot.player.age + 1
                if next_age >= GameplayConstants.RETIREMENT_AGE.value:
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

    def _decision_required(self, cmp: AbstractCompetition, clubs: Dict[str, Club]) -> bool:
        if cmp is None or not cmp.current_matches:
            return False

        for match in cmp.current_matches:
            if self._manager_club_id not in (match.home_pk, match.away_pk):
                continue
            if not clubs[self._manager_club_id].has_selected_player:
                return True

        return False

    @property
    def _clubs(self) -> Dict[str, Club]:
        repo = TemporalClubProvider.get_instance()
        return repo.get_clubs_for_game(self._game_id)

    @property
    def _training_check(self) -> bool:
        cmp = self.cmp
        if cmp is None or cmp.current_matches:
            return True

        if _get_competition_type(cmp) != CompetitionType.CHAMPIONSHIP:
            return True

        def check_club(c: Club) -> bool:
            return self._calculate_club_practice_cost(c) <= c.account.balance

        for club in self._clubs.values():
            if not self._is_manager_club(club.club_id):
                continue
            if not check_club(club):
                return False
        return True

    def _calculate_club_practice_cost(self, club: Club) -> int:
        slots = [(s.player.level, s.coach_level) for s in club.players if s.player is not None]
        return sum(self._practice_calculator(*slot) for slot in slots)

    def _get_opponent(self, cmp: Optional[AbstractCompetition], pk: str) -> Optional[OpponentDto]:
        def schedule_filter(pair: ScheduledMatch):
            if pair.home_pk == pk:
                return True
            return pair.away_pk == pk

        if cmp is None or cmp.is_over:
            return None

        schedule = cmp.current_matches
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
            if slot.player is None:
                raise RuntimeError("")
            slot.contract_cost = self._contract_calculator(slot.player.level)
            return slot

        return [set_contract_prices(slot) for slot in self._clubs[pk].players if slot.player is not None]

    def _hire_players_if_needed(self, clubs: Dict[str, Club]) -> List[Contract]:
        res = []

        for master_club in clubs.values():
            if master_club.farm_club_id is None:
                continue
            if self._is_manager_club(master_club.club_id):
                continue

            res.extend(self._hire_until_roster_is_full(master_club))

        return res

    def _hire_until_roster_is_full(self, club: Club) -> List[Contract]:
        new_contracts = []

        while len(club.players) < GameplayConstants.PLAYERS_PER_CLUB_SYSTEM.value:
            player = self._player_factory.create_player(
                level=0,
                age=GameplayConstants.STARTING_AGE.value,
            )
            club.add_player(player)
            contract_cost = self._contract_calculator(player.level)
            new_contracts.extend((
                Contract(
                    self._game_id,
                    club.club_id,
                    player.player_id,
                    self._season_index,
                    contract_cost,
                    "active",
                ),
                Contract(
                    self._game_id,
                    club.club_id,
                    player.player_id,
                    self._season_index + 1,
                    contract_cost,
                    "future",
                ),
            ))

        return new_contracts

    def _assign_players(self, clubs: Dict[str, Club]):
        for main_club in clubs.values():
            farm_club = _get_farm_club(main_club.club_id, clubs)

            if farm_club is None:
                continue
            if self._is_manager_club(main_club.club_id):
                continue

            players = [
                slot.player
                for club in (main_club, farm_club)
                for slot in club.players
                if slot.player is not None
            ]
            players.sort(key=lambda plr: plr.level, reverse=True)
            main_player_count = len(players) // 2

            for club in (main_club, farm_club):
                for slot in club.players:
                    if slot.player is not None:
                        club.pop_player(slot.player.player_id)

            for player in players[:main_player_count]:
                main_club.add_player(player)
            for player in players[main_player_count:]:
                farm_club.add_player(player)

    def _is_club_valid(self, pk: str, club: Club, cmp: Optional[AbstractCompetition]) -> bool:
        if cmp is None:
            return True

        opponent = self._get_opponent(cmp, pk)
        if opponent is None or not self._is_manager_club(pk):
            return True

        best_player = max(
            [slot.player.actual_technique for slot in club.players if slot.player is not None],
            default=0,
        )

        min_player_contract = self._contract_calculator(level=0)
        if best_player <= 0 and club.account.balance < min_player_contract:
            return False

        if opponent.player is None:
            return True

        return True

    def _next_season(self, clubs: Dict[str, Club]):
        # TODO: Fix fame calculation

        self._shuffle_coach_powers(clubs)
        self._reset_current_date_to_next_season_start()
        self._season_index += 1
        _process_season_end_players(clubs)
        self._start_regular_championship(clubs)

    def _perform_practice(self, clubs: Dict[str, Club]):
        if not self._can_practice:
            return

        for club in clubs.values():
            if self._is_manager_club(club.club_id):
                club.account.ProcessTransaction(DdTransaction(
                    -self._calculate_club_practice_cost(club),
                    f"Practice on {self._formatted_current_date}"
                ))
            club.perform_practice()

    def _play_one_day(self, clubs: Dict[str, Club]):
        repo = CompetitionRepository.tmp_get_instance()
        scheduled_matches_repository = ScheduledMatchRepository.tmp_get_instance()
        match_result_repository = MatchResultRepository.tmp_get_instance()

        competitions = repo.get_ongoing_competitions(self._game_id)

        playing_player_ids: List[str] = []

        for competition in competitions:
            current_matches = scheduled_matches_repository.get_matches_for_competition(
                self._game_id,
                competition.competition_id,
                competition.day,
            )

            playing_player_ids.extend(_get_playing_player_ids(current_matches, clubs))
            results = process_matches(
                current_matches, clubs, competition.match_params
            )

            competition.apply_results(results)

            for match in current_matches:
                match.set_played()

            scheduled_matches_repository.save_matches(
                self._game_id,
                competition.get_full_schedule(),
            )
            match_result_repository.save_match_results(self._game_id, results)
            repo.save_competition(self._game_id, competition, self._season_index)

        # TODO: Remove these from here
        _calculate_match_income(clubs)
        self._recover(clubs=clubs, excluded_player_ids=set(playing_player_ids))

    def _recover(self, clubs: Dict[str, Club], excluded_player_ids: Set[str]):
        recovery_function = ExhaustedLinearRecovery(
            self._params.exhaustion_factor
        )
        for club in clubs.values():
            for slot in club.players:
                if slot.player is None or slot.player.player_id in excluded_player_ids:
                    continue
                slot.player.recover_stamina(
                    recovery_function(slot.player)
                )

    def _is_manager_club(self, club_id: str) -> bool:
        return self._manager_club_id == club_id

    @property
    def _manager_club_in_current_competition(self) -> bool:
        cmp = self.cmp
        if cmp is None:
            return False

        if self._manager_club_id is None:
            return True
        return cmp.contains_club(self._manager_club_id)

    @property
    def _formatted_current_date(self) -> str:
        return self._current_date.strftime("%Y-%b-%d")

    def _advance_current_date(self):
        self._current_date += timedelta(days=1)

    def _reset_current_date_to_next_season_start(self):
        self._current_date = date(
            self._current_date.year + 1,
            _SEASON_START_MONTH,
            _SEASON_START_DAY,
        ) - timedelta(days=1)

    def _save_competition_results(self):
        pass

    def _start_playoff(self):
        repo = CompetitionRepository.tmp_get_instance()
        scheduled_matches_repository = ScheduledMatchRepository.tmp_get_instance()
        regulars = self._get_regular_championships()

        for regular in regulars:
            playoffs = Playoff(
                self._params.playoff_params,
                _make_playoff_seeds(
                    regular.standings,
                    self._params.playoff_params.length,
                ),
            )
            repo.save_competition(
                game_id=self._game_id,
                competition=playoffs,
                season_index=self._season_index,
            )
            scheduled_matches_repository.save_matches(
                self._game_id,
                playoffs.get_full_schedule(),
            )

    def _start_regular_championship(self, clubs: Dict[str, Club]):
        competition_repository = CompetitionRepository.tmp_get_instance()
        match_repository = ScheduledMatchRepository.tmp_get_instance()

        clubs_by_league = {}
        for club in clubs.values():
            clubs_by_league.setdefault(club.league_id, []).append(club.club_id)

        for league_id, club_ids in clubs_by_league.items():
            if league_id not in _COMPETITION_LEAGUE_IDS:
                continue

            competition = RegularChampionship(
                club_ids,
                self._params.championship_params,
            )
            competition.make_schedule()
            competition_repository.save_competition(
                game_id=self._game_id,
                competition=competition,
                season_index=self._season_index,
            )
            match_repository.save_matches(
                self._game_id,
                competition.get_full_schedule(),
            )

    def _get_regular_championships(self) -> List[AbstractCompetition]:
        repo = CompetitionRepository.tmp_get_instance()
        cmps = repo.get_season_competitions(self._game_id, self._season_index)

        return [c for c in cmps if isinstance(c, RegularChampionship)]

    def _update_season_fame(self):
        # TODO: Fix fame calculation
        pass

    # This whole method is a temporary hack before I'll implement a proper AI
    def _shuffle_coach_powers(self, clubs: Dict[str, Club]):
        from random import shuffle
        strong_clubs = [pk for pk, club in clubs.items() if
                        club.coach_power == 3 and not self._is_manager_club(pk)]
        medium_clubs = [pk for pk, club in clubs.items() if
                        club.coach_power == 2 and not self._is_manager_club(pk)]
        weaksy_clubs = [pk for pk, club in clubs.items() if
                        club.coach_power == 1 and not self._is_manager_club(pk)]

        shuffle(strong_clubs)
        shuffle(medium_clubs)
        shuffle(weaksy_clubs)

        while len(strong_clubs) > 5:
            medium_clubs.append(strong_clubs.pop())

        while len(medium_clubs) > 6:
            weaksy_clubs.append(medium_clubs.pop())

        s, m, w = strong_clubs.pop(), medium_clubs.pop(), weaksy_clubs.pop()
        s, m, w = m, w, s  # cycle

        logging.debug(f"Strong club going weak:   {clubs[s].name}")
        logging.debug(f"Medium club going strong: {clubs[m].name}")
        logging.debug(f"Weak club going medium:   {clubs[w].name}")

        strong_clubs.append(s)
        medium_clubs.append(m)
        weaksy_clubs.append(w)

        [clubs[pk].set_coach_power(3) for pk in strong_clubs]
        [clubs[pk].set_coach_power(2) for pk in medium_clubs]
        [clubs[pk].set_coach_power(1) for pk in weaksy_clubs]

        for master_club in clubs.values():
            if master_club.farm_club_id is None:
                continue
            farm_club = clubs.get(master_club.farm_club_id)
            if farm_club is not None:
                farm_club.set_coach_power(master_club.coach_power)


def _make_playoff_seeds(
        standings: List[DdStandingsRowStruct],
        playoff_length: int,
) -> List[PlayoffSeed]:
    return [
        PlayoffSeed(club_id=row.club_id, seed=seed)
        for seed, row in enumerate(standings[:playoff_length], start=1)
    ]


def _process_season_end_players(clubs: Dict[str, Club]):
    for club in clubs.values():
        for slot in club.players:
            player = slot.player
            if player is None:
                continue
            player.age_up()
            player.after_season_rest()
        club.process_end_of_season_contracts()
        club.expel_retired_players()


def _unselect(clubs: Dict[str, Club]):
    for club in clubs.values():
        club.select_player(None)


def _get_competition_type(cmp: Optional[AbstractCompetition]) -> Optional[CompetitionType]:
    if isinstance(cmp, RegularChampionship):
        return CompetitionType.CHAMPIONSHIP
    elif isinstance(cmp, Playoff):
        return CompetitionType.PLAY_OFFS
    elif cmp is None:
        return None
    raise RuntimeError(f"Unknown competition type. {type(cmp).__name__}")


def _has_matches(cmp: Optional[AbstractCompetition]) -> bool:
    if cmp is None:
        return False

    return len(cmp.current_matches) > 0


def _get_remaining_matches(competition: Optional[AbstractCompetition], club_id: str) -> List[Optional[ScheduledMatch]]:
    if competition is None:
        return []

    return competition.get_club_schedule_days(club_id)


def _get_competition_title(competition: Optional[AbstractCompetition]) -> str:
    if competition is None:
        return ""

    return competition.title


def _calculate_match_income(clubs: Dict[str, Club]):
    for club in clubs.values():
        club.account.ProcessTransaction(DdTransaction(
            value=250_000,
            comment="Income"
        ))


def _get_playing_player_ids(matches: List[ScheduledMatch], clubs: Dict[str, Club]) -> Set[str]:
    player_ids = set()
    for match in matches:
        for club_id in (match.home_pk, match.away_pk):
            player = clubs[club_id].selected_player
            if player is not None:
                player_ids.add(player.player_id)

    return player_ids


def _get_farm_club(club_id: str, clubs: Dict[str, Club]) -> Optional[Club]:
    if club_id not in clubs:
        return None

    fk_id = clubs[club_id].farm_club_id

    if fk_id is None:
        return None

    return clubs.get(fk_id, None)
