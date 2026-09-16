"""
Created September 14, 2026

@author montreal91

Tests for selecting a player for the next match.
"""

import sqlite3

from core.ports.inbound.commands.create_new_game import init_clubs_for_game
from core.ports.inbound.commands.select_player_for_match import (
    SelectPlayerForMatchCommand,
)
from core.ports.inbound.commands.select_player_for_match import (
    SelectPlayerForMatchCommandHandler,
)
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from persistence.migration_history import init_db
from tests.core.fixtures.game import make_game


def test_select_player_for_match_persists_selected_player(tmp_path):
    db_path = tmp_path / "select-player-for-match.sqlite"
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
    player_id = game.clubs[club_id].players[0].player.player_id
    handler = SelectPlayerForMatchCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(SelectPlayerForMatchCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    persisted_player_id = conn.execute(
        """
        SELECT selected_player_id
        FROM club
        WHERE game_id = ? AND club_id = ?
        """,
        ("game", club_id),
    ).fetchone()[0]
    assert result.success
    assert persisted_player_id == player_id
