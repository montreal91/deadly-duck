"""
Created September 19, 2026

@author montreal91

Tests for firing a roster player.
"""

from unittest.mock import Mock

from core.ports.inbound.commands.fire_player import FirePlayerCommand
from core.ports.inbound.commands.fire_player import FirePlayerCommandHandler
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from tests.core.fixtures.game import make_persisted_game


def test_fire_player_command_persists_roster_removal(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "fire-player.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    player_id = clubs[club_id].players[0].player.player_id
    handler = FirePlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
    )

    result = handler(FirePlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    roster_entry_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM roster_entry
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    ).fetchone()[0]
    player_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM player
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    ).fetchone()[0]
    assert result.success
    assert roster_entry_count == 0
    assert player_count == 1


def test_fire_player_command_rejects_missing_game_without_saving():
    game_repository = Mock()
    game_repository.does_game_exist.return_value = False
    club_provider = Mock()
    handler = FirePlayerCommandHandler(game_repository, club_provider)

    result = handler(FirePlayerCommand(
        game_id="missing-game",
        club_id="club",
        player_id="player",
    ))

    assert not result.success
    assert result.message == "Game not found"
    game_repository.save_game.assert_not_called()
    club_provider.save_club.assert_not_called()
