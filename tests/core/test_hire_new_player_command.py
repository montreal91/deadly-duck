"""
Created September 14, 2026

@author montreal91

Tests for hiring a newly generated player.
"""

import sqlite3

from core.ports.inbound.commands.create_new_game import init_clubs_for_game
from core.ports.inbound.commands.hire_new_player import HireNewPlayerCommand
from core.ports.inbound.commands.hire_new_player import HireNewPlayerCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from persistence.migration_history import init_db
from tests.core.fixtures.game import make_game_params
from tests.core.fixtures.game import make_game


def test_hire_new_player_adds_player_and_charges_club(tmp_path):
    db_path = tmp_path / "hire-new-player.sqlite"
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    CompetitionRepository.tmp_initialize(conn)
    ScheduledMatchRepository.tmp_init(conn)
    MatchResultRepository.tmp_init(conn)
    TemporalClubProvider.initialize(conn)
    conn.execute("INSERT INTO game (game_id) VALUES ('game')")
    conn.commit()

    club_provider = TemporalClubProvider.get_instance()
    club_provider.save_clubs(init_clubs_for_game("game").values())
    game = make_game(game_id="game", conn=conn)
    club_provider = TemporalClubProvider.get_instance()
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(game.clubs))
    initial_club = game.clubs[club_id]
    initial_player_count = len(initial_club.players)
    initial_balance = initial_club.account.balance
    handler = HireNewPlayerCommandHandler(
        game_repository,
        club_provider,
        make_game_params(),
    )

    result = handler(HireNewPlayerCommand(game_id="game", club_id=club_id))

    persisted_club = TemporalClubProvider(conn).get_clubs_for_game("game")[club_id]
    assert result.success
    assert len(persisted_club.players) == initial_player_count + 1
    assert persisted_club.account.balance == initial_balance - 10_000
