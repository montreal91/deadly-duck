"""
Created September 14, 2026

@author montreal91
"""
import sqlite3
import time

from core.game import Game
from core.game import GameParams
from core.match import DdLinearProbabilityCalculator
from core.match import ExhaustionCalculator
from core.match_engine import MatchParams
from core.player import PlayerReputationCalculator
from core.playoffs import PlayoffParams
from core.ports.inbound.commands.create_new_game import init_clubs_for_game
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.player_repository import PlayerRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.regular_championship import ChampionshipParams
from persistence.migration_history import init_db


def make_game(game_id: str, conn=None) -> Game:
    TemporalClubProvider.initialize(conn)
    now = time.time_ns() // 1_000_000
    return Game(
        params=make_game_params(),
        game_id=game_id,
        created_ts=now,
        updated_ts=now,
    )


def make_persisted_game(game_id, db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    CompetitionRepository.tmp_initialize(conn)
    ScheduledMatchRepository.tmp_init(conn)
    MatchResultRepository.tmp_init(conn)
    PlayerRepository.tmp_init(conn)
    TemporalClubProvider.initialize(conn)
    conn.execute("INSERT INTO game (game_id) VALUES (?)", (game_id,))
    conn.commit()
    TemporalClubProvider.get_instance().save_clubs(
        init_clubs_for_game(game_id).values()
    )

    game = make_game(game_id=game_id, conn=conn)
    clubs = TemporalClubProvider.get_instance().get_clubs_for_game(game_id)
    return game, clubs, conn

def make_game_params() -> GameParams:
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
