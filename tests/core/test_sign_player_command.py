"""
Created September 18, 2026

@author montreal91

Tests for signing a player for the next season.
"""

from unittest.mock import Mock

from core.ports.inbound.commands.sign_player import SignPlayerCommand
from core.ports.inbound.commands.sign_player import SignPlayerCommandHandler
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from tests.core.fixtures.game import make_game_params
from tests.core.fixtures.game import make_persisted_game


def test_sign_player_command_persists_contract_and_payment(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "sign-player.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    club = clubs[club_id]
    player_id = club.players[0].player.player_id
    initial_balance = club.account.balance
    conn.execute(
        """
        UPDATE roster_entry
        SET has_next_contract = 0
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    )
    conn.commit()
    handler = SignPlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        make_game_params(),
    )

    result = handler(SignPlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    persisted_contract = conn.execute(
        """
        SELECT has_next_contract
        FROM roster_entry
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    ).fetchone()[0]
    persisted_balance = conn.execute(
        """
        SELECT balance
        FROM club
        WHERE game_id = ? AND club_id = ?
        """,
        ("game", club_id),
    ).fetchone()[0]
    assert result.success
    assert persisted_contract == 1
    assert persisted_balance == initial_balance - 10_000


def test_sign_player_command_does_not_save_when_player_is_already_signed(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "already-signed-player.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    player_id = clubs[club_id].players[0].player.player_id
    club_provider = Mock(wraps=TemporalClubProvider.get_instance())
    handler = SignPlayerCommandHandler(
        game_repository,
        club_provider,
        make_game_params(),
    )

    result = handler(SignPlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    assert not result.success
    assert result.message == "This player already has a contract for the next season."
    club_provider.save_club.assert_not_called()
