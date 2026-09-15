"""
Created September 14, 2026

@author montreal91
"""
import time

from core.game import Game
from core.game import GameParams
from core.match import DdLinearProbabilityCalculator
from core.match import ExhaustionCalculator
from core.match_engine import MatchParams
from core.player import PlayerReputationCalculator
from core.playoffs import PlayoffParams
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.regular_championship import ChampionshipParams


def make_game(game_id: str) -> Game:
    TemporalClubProvider.initialize()
    now = time.time_ns() // 1_000_000
    return Game(
        params=_game_params(),
        game_id=game_id,
        created_ts=now,
        updated_ts=now,
    )

def _game_params():
    match_params = MatchParams(
        games_to_win=1,
        sets_to_win=1,
        exhaustion_function=ExhaustionCalculator(1),
        probability_function=DdLinearProbabilityCalculator(0.003),
        reputation_function=PlayerReputationCalculator(1, 1),
    )
    return GameParams(
        championship_params=ChampionshipParams(
            match_params=match_params,
            recovery_day=2,
            rounds=2,
            match_importance=1,
        ),
        playoff_params=PlayoffParams(
            series_matches_pattern=(True, True, False),
            length=8,
            gap_days=0,
            match_params=match_params,
            match_importance=1,
        ),
        contracts=[10000 for _ in range(30)],
        exhaustion_factor=8,
        is_hard=False,
        training_coefficient=1,
        years_to_simulate=0,
    )
