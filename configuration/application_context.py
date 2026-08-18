"""
Dependency injection stuff.

Created May 11, 2024

@author montreal91
"""
import configparser
import json
from pathlib import Path
from sqlite3 import connect

from core.ports.inbound.commands.fire_player import FirePlayerCommandHandler
from core.ports.inbound.commands.hire_new_player import HireNewPlayerCommandHandler
from core.ports.inbound.commands.next_day import NextDayCommandHandler
from core.ports.inbound.commands.sign_player import SignPlayerCommandHandler
from core.ports.inbound.commands.select_coach_for_player import SelectCoachForPlayerCommandHandler
from core.ports.outbound.club_repository import ClubRepository
from core.game import GameParams
from core.game_service import FameQueryHandler
from core.game_service import GameService
from core.match import DdExhaustionCalculator
from core.match import DdLinearProbabilityCalculator
from core.match import DdMatchParams
from core.player import DdPlayerReputationCalculator
from core.playoffs import DdPlayoffParams
from core.ports.inbound.commands.create_new_game import CreateNewGameCommandHandler
from core.ports.inbound.commands.select_club import SelectClubCommandHandler
from core.ports.outbound.game_repository import GameRepository
from core.queries.club_selection_screen_query import ClubSelectionScreenQueryHandler
from core.queries.day_results_query import DayResultsQueryHandler
from core.queries.main_screen_query import GameScreenGuiQueryHandler
from core.queries.practice_screen_query import PracticeScreenQueryHandler
from core.queries.roster_management_screen_query import RosterManagementScreenQueryHandler
from core.regular_championship import ChampionshipParams


def _make_db_connection(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return connect(db_path)


class ApplicationContext:
    def __init__(self):
        self._db_connection = _make_db_connection("data/duck.db")
        self._game_repository = GameRepository(self._db_connection)
        self._club_repository = ClubRepository(self._game_repository)
        self._params = _get_params()
        self._fame_query_handler = FameQueryHandler(self._club_repository)

        self._create_game_command_handler = CreateNewGameCommandHandler(
            self._game_repository,
            self._params,
        )

        self._select_club_command_handler = SelectClubCommandHandler(self._game_repository)

        self._club_selection_screen_query_handler = ClubSelectionScreenQueryHandler(
            club_repository=self._club_repository,
        )

        self._next_day_command_handler = NextDayCommandHandler(self._game_repository)

        self._game_service = GameService(
            game_repository=self._game_repository,
            game_parameters=self._params,
            fame_query_handler=self._fame_query_handler,
        )

        self._game_screen_ui_query_handler = GameScreenGuiQueryHandler(
            self._game_repository,
            self._club_repository
        )

        self._day_results_query_handler = DayResultsQueryHandler(
            self._game_repository,
            self._club_repository,
        )

        self._roster_management_screen_query_handler = RosterManagementScreenQueryHandler(
            self._game_repository,
        )

        self._practice_screen_query_handler = PracticeScreenQueryHandler(
            self._game_repository,
        )

        self._hire_new_player_command_handler = HireNewPlayerCommandHandler(
            self._game_repository,
        )

        self._sign_player_command_handler = SignPlayerCommandHandler(
            self._game_repository,
        )

        self._fire_player_command_handler = FirePlayerCommandHandler(
            self._game_repository,
        )

        self._select_coach_for_player_command_handler = SelectCoachForPlayerCommandHandler(
            self._game_repository,
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
    def hire_new_player_command_handler(self):
        return self._hire_new_player_command_handler

    @property
    def sign_player_command_handler(self):
        return self._sign_player_command_handler

    @property
    def fire_player_command_handler(self):
        return self._fire_player_command_handler

    @property
    def select_coach_for_player_command_handler(self):
        return self._select_coach_for_player_command_handler


def _get_params() -> GameParams:
    path = "configuration/short.ini"
    config = configparser.ConfigParser()
    config.read(path)
    match_params = DdMatchParams(
        speciality_bonus=config["match"].getfloat("speciality_bonus", 0.0),
        games_to_win=config["match"].getint("games_to_win", 0),
        sets_to_win=config["match"].getint("sets_to_win", 0),
        exhaustion_function=DdExhaustionCalculator(
            config["match"].getint("exhaustion_coefficient", 0)
        ),
        reputation_function=DdPlayerReputationCalculator(
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
    playoff_params = DdPlayoffParams(
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
