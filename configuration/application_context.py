"""
Dependency injection stuff.

Created May 11, 2024

@author montreal91
"""

import configparser
import json

from core.game_repostory import GameRepository
from core.game_service import GameService, ClubRepository, FameQueryHandler
from core.game import GameParams
from core.match import DdMatchParams
from core.match import DdExhaustionCalculator
from core.player import DdPlayerReputationCalculator
from core.match import DdLinearProbabilityCalculator
from core.attendance import DdAttendanceParams
from core.regular_championship import DdChampionshipParams
from core.playoffs import DdPlayoffParams
from core.attendance import DdCourt


class ApplicationContext:
    def __init__(self):
        self._game_repository = GameRepository()
        self._club_repository = ClubRepository(self._game_repository)
        self._params = _get_params()
        self._fame_query_handler = FameQueryHandler(self._club_repository)
        self._game_service = GameService(
            game_repository=self._game_repository,
            game_parameters=self._params,
            fame_query_handler=self._fame_query_handler,
        )

    @property
    def game_service(self):
        return self._game_service

    @property
    def game_parameters(self):
        return self._params


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
    attendance_params = DdAttendanceParams(
        price=config["attendance"].getfloat("price", 0.0),
        home_fame=config["attendance"].getfloat("home_fame", 0.0),
        away_fame=config["attendance"].getfloat("away_fame", 0.0),
        reputation=config["attendance"].getfloat("reputation", 0.0),
        importance=config["attendance"].getfloat("importance", 0.0),
    )
    championship_params = DdChampionshipParams(
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
        attendance_params=attendance_params,
        championship_params=championship_params,
        playoff_params=playoff_params,
        courts=dict(
            default=DdCourt(capacity=1000, rent_cost=1000),
            tiny=DdCourt(capacity=1000, rent_cost=1000),
            small=DdCourt(capacity=2000, rent_cost=5000),
            medium=DdCourt(capacity=4000, rent_cost=16000),
            big=DdCourt(capacity=8000, rent_cost=44000),
            huge=DdCourt(capacity=16000, rent_cost=112000)
        ),
        contracts=json.loads(config.get("game", "contracts")),
        exhaustion_factor=config["game"].getint("exhaustion_factor", 0),
        is_hard=config["game"].getboolean("is_hard", True),
        training_coefficient=config["game"].getint("training_coefficient", 0),
        years_to_simulate=config["game"].getint("years_to_simulate", 0),
    )


_ac = ApplicationContext()


def get_application_context():
    return _ac
