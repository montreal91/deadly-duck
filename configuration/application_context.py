"""
Dependency injection stuff.

Created May 11, 2024

@author montreal91
"""
import configparser
import json
from pathlib import Path
from sqlite3 import connect
from sqlite3 import Row

from core.match_engine import MatchParams
from core.ports.inbound.commands.fire_player import FirePlayerCommandHandler
from core.ports.inbound.commands.assign_player import AssignPlayerCommandHandler
from core.ports.inbound.commands.hire_new_player import HireNewPlayerCommandHandler
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommandHandler,
)
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.inbound.commands.select_player_for_match import SelectPlayerForMatchCommandHandler
from core.ports.inbound.commands.sign_player import SignPlayerCommandHandler
from core.ports.inbound.commands.select_coach_for_player import SelectCoachForPlayerCommandHandler
from core.game import GameParams
from core.game_service import GameService
from core.match import ExhaustionCalculator
from core.match import DdLinearProbabilityCalculator
from core.player import PlayerReputationCalculator
from core.playoffs import PlayoffParams
from core.ports.inbound.commands.create_new_game import CreateNewGameCommandHandler
from core.ports.inbound.commands.select_club import SelectClubCommandHandler
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.player_repository import PlayerRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.queries.club_selection_screen_query import ClubSelectionScreenQueryHandler
from core.queries.day_results_query import DayResultsQueryHandler
from core.queries.game_screen_query import GameScreenGuiQueryHandler
from core.queries.level_up_screen_query import LevelUpScreenQueryHandler
from core.queries.player_details_screen_query import PlayerDetailsScreenQueryHandler
from core.queries.practice_screen_query import PracticeScreenQueryHandler
from core.queries.roster_management_screen_query import RosterManagementScreenQueryHandler
from core.regular_championship import ChampionshipParams
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


def _make_db_connection(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect(db_path)
    conn.row_factory = Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


class ApplicationContext:
    def __init__(self):
        self._db_connection = _make_db_connection("data/duck.db")

        TemporalClubProvider.initialize(self._db_connection)
        CompetitionRepository.tmp_initialize(self._db_connection)
        ScheduledMatchRepository.tmp_init(self._db_connection)
        MatchResultRepository.tmp_init(self._db_connection)
        PlayerRepository.tmp_init(self._db_connection)
        ContractRepository.tmp_init(self._db_connection)

        self._temporal_club_provider = TemporalClubProvider.get_instance()
        self._competition_repository = CompetitionRepository.tmp_get_instance()
        self._scheduled_match_repository = ScheduledMatchRepository.tmp_get_instance()
        self._match_result_repository = MatchResultRepository.tmp_get_instance()

        self._game_repository = GameRepository(
            self._db_connection,
        )
        self._player_repository = PlayerRepository.tmp_get_instance()
        self._contract_repository = ContractRepository.tmp_get_instance()
        self._player_assignment_repository = PlayerAssignmentRepository(
            self._db_connection,
        )
        self._assign_player_command_handler = AssignPlayerCommandHandler(
            self._temporal_club_provider,
            self._player_assignment_repository,
        )
        self._params = _get_params()

        self._create_game_command_handler = CreateNewGameCommandHandler(
            self._game_repository,
            self._params,
            self._temporal_club_provider,
            self._player_assignment_repository,
            self._contract_repository,
        )

        self._select_club_command_handler = SelectClubCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
        )

        self._club_selection_screen_query_handler = ClubSelectionScreenQueryHandler(
            club_provider=self._temporal_club_provider,
        )

        self._next_day_command_handler = NextDayCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._competition_repository,
            self._contract_repository,
        )

        self._game_service = GameService(
            game_repository=self._game_repository,
            game_parameters=self._params,
            competition_repository=self._competition_repository,
        )

        self._game_screen_ui_query_handler = GameScreenGuiQueryHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._match_result_repository,
            self._competition_repository,
        )

        self._day_results_query_handler = DayResultsQueryHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._competition_repository,
            self._match_result_repository,
        )

        self._roster_management_screen_query_handler = RosterManagementScreenQueryHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._player_assignment_repository,
        )

        self._practice_screen_query_handler = PracticeScreenQueryHandler(
            self._game_repository,
        )

        self._player_details_screen_query_handler = PlayerDetailsScreenQueryHandler(
            self._player_repository,
        )

        self._level_up_screen_query_handler = LevelUpScreenQueryHandler(
            self._temporal_club_provider,
        )

        self._hire_new_player_command_handler = HireNewPlayerCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._params,
            self._contract_repository,
            self._player_assignment_repository,
        )

        self._sign_player_command_handler = SignPlayerCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
            self._params,
            self._contract_repository,
        )

        self._fire_player_command_handler = FirePlayerCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
        )

        self._select_coach_for_player_command_handler = SelectCoachForPlayerCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
        )

        self._select_player_for_match_command_handler = SelectPlayerForMatchCommandHandler(
            self._game_repository,
            self._temporal_club_provider,
        )

        self._improve_player_skill_command_handler = ImprovePlayerSkillCommandHandler(
            self._game_repository,
            self._player_repository,
        )

    @property
    def game_service(self):
        return self._game_service

    @property
    def next_day_command_handler(self):
        return self._next_day_command_handler

    @property
    def game_parameters(self):
        return self._params

    @property
    def create_game_command_handler(self):
        return self._create_game_command_handler

    @property
    def select_club_command_handler(self):
        return self._select_club_command_handler

    @property
    def select_club_screen_query_handler(self):
        return self._club_selection_screen_query_handler

    @property
    def game_screen_ui_query_handler(self):
        return self._game_screen_ui_query_handler

    @property
    def day_results_query_handler(self):
        return self._day_results_query_handler

    @property
    def roster_management_screen_query_handler(self):
        return self._roster_management_screen_query_handler

    @property
    def practice_screen_query_handler(self):
        return self._practice_screen_query_handler

    @property
    def player_details_screen_query_handler(self):
        return self._player_details_screen_query_handler

    @property
    def level_up_screen_query_handler(self):
        return self._level_up_screen_query_handler

    @property
    def hire_new_player_command_handler(self):
        return self._hire_new_player_command_handler

    @property
    def sign_player_command_handler(self):
        return self._sign_player_command_handler

    @property
    def fire_player_command_handler(self):
        return self._fire_player_command_handler

    @property
    def assign_player_command_handler(self):
        return self._assign_player_command_handler

    @property
    def select_coach_for_player_command_handler(self):
        return self._select_coach_for_player_command_handler

    @property
    def select_player_for_match_command_handler(self):
        return self._select_player_for_match_command_handler

    @property
    def improve_player_skill_command_handler(self):
        return self._improve_player_skill_command_handler


def _get_params() -> GameParams:
    path = "configuration/short.ini"
    config = configparser.ConfigParser()
    config.read(path)
    match_params = MatchParams(
        games_to_win=config["match"].getint("games_to_win", 0),
        sets_to_win=config["match"].getint("sets_to_win", 0),
        exhaustion_function=ExhaustionCalculator(
            config["match"].getint("exhaustion_coefficient", 0)
        ),
        reputation_function=PlayerReputationCalculator(
            config["match"].getint("games_to_win", 0),
            config["match"].getint("reputation_coefficient", 0)
        ),
        probability_function=DdLinearProbabilityCalculator(
            config["match"].getfloat("probability_coefficient", 0.0)
        ),
    )

    championship_params = ChampionshipParams(
        match_params=match_params,
        recovery_day=config["championship"].getint("recovery_day", 0),
        rounds=config["championship"].getint("rounds", 0),
        match_importance=config["championship"].getint(
            "match_importance", 0
        ),
    )
    playoff_params = PlayoffParams(
        series_matches_pattern=(
            True, True, False, False, True, False, True,
        ),
        match_params=match_params,
        length=config["playoff"].getint("length", 0),
        gap_days=config["playoff"].getint("gap_days", 0),
        match_importance=config["playoff"].getint("match_importance", 0),
    )
    return GameParams(
        championship_params=championship_params,
        playoff_params=playoff_params,
        contracts=json.loads(config.get("game", "contracts")),
        exhaustion_factor=config["game"].getint("exhaustion_factor", 0),
        is_hard=config["game"].getboolean("is_hard", True),
        training_coefficient=config["game"].getint("training_coefficient", 0),
        years_to_simulate=config["game"].getint("years_to_simulate", 0),
    )


_ac = ApplicationContext()


def get_application_context():
    return _ac
