"""
Created September 19, 2026

@author montreal91

Tests for firing a roster player.
"""

from unittest.mock import Mock

from core.ports.inbound.commands.fire_player import FirePlayerCommand
from core.ports.inbound.commands.fire_player import FirePlayerCommandHandler
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from tests.core.fixtures.game import make_persisted_game


def test_fire_player_command_persists_roster_removal(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "fire-player.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club = clubs["darwin_ducks"]
    game._manager_club_id = club.club_id
    game_repository.save_game(game)
    player_id = club.players[0].player.player_id
    contracts = ContractRepository(conn)
    contracts.create_active_contract(
        game.game_id, club.club_id, player_id, game.season_index, 10_000,
    )
    contracts.create_future_contract(
        game.game_id, club.club_id, player_id, game.season_index + 1, 10_000,
    )
    handler = FirePlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        contracts,
    )

    result = handler(FirePlayerCommand(
        game_id="game",
        club_id=club.club_id,
        player_id=player_id,
    ))

    roster_entry_count = conn.execute(
        """
        SELECT COUNT(*)
            FROM player_assignment
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
    contract_statuses = conn.execute(
        """
        SELECT status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        ORDER BY season_index
        """,
        ("game", player_id),
    ).fetchall()
    assert result.success
    assert roster_entry_count == 0
    assert player_count == 1
    assert [row[0] for row in contract_statuses] == [
        "terminated",
        "terminated",
    ]


def test_fire_player_command_allows_firing_farm_player(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "fire-farm-player.sqlite",
    )
    master_club = clubs["darwin_ducks"]
    farm_club = clubs[master_club.farm_club_id]
    player_id = master_club.players[0].player.player_id
    PlayerAssignmentRepository(conn).assign_player(
        game.game_id,
        farm_club.club_id,
        player_id,
    )
    game._manager_club_id = master_club.club_id
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    contracts = ContractRepository(conn)
    contracts.create_active_contract(
        game.game_id,
        master_club.club_id,
        player_id,
        game.season_index,
        10_000,
    )
    contracts.create_future_contract(
        game.game_id,
        master_club.club_id,
        player_id,
        game.season_index + 1,
        10_000,
    )
    handler = FirePlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        contracts,
    )

    result = handler(FirePlayerCommand(
        game_id=game.game_id,
        club_id=farm_club.club_id,
        player_id=player_id,
    ))

    assignment_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM player_assignment
        WHERE game_id = ? AND player_id = ?
        """,
        (game.game_id, player_id),
    ).fetchone()[0]
    contract_statuses = conn.execute(
        """
        SELECT status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        ORDER BY season_index
        """,
        (game.game_id, player_id),
    ).fetchall()
    assert result.success
    assert assignment_count == 0
    assert [row[0] for row in contract_statuses] == [
        "terminated",
        "terminated",
    ]


def test_fire_player_command_rejects_player_from_non_controlled_club(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "fire-other-club-player.sqlite",
    )
    controlled_club = clubs["darwin_ducks"]
    other_club = clubs["auckland_aces"]
    player_id = other_club.players[0].player.player_id
    game._manager_club_id = controlled_club.club_id
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    contract_repository = Mock()
    club_provider = Mock(wraps=TemporalClubProvider.get_instance())
    handler = FirePlayerCommandHandler(
        game_repository,
        club_provider,
        contract_repository,
    )

    result = handler(FirePlayerCommand(
        game_id=game.game_id,
        club_id=other_club.club_id,
        player_id=player_id,
    ))

    assert not result.success
    assert result.message == "Incorrect club id."
    club_provider.save_club.assert_not_called()
    contract_repository.terminate_player_contracts.assert_not_called()


def test_fire_player_command_rejects_missing_game_without_saving():
    game_repository = Mock()
    game_repository.does_game_exist.return_value = False
    club_provider = Mock()
    contract_repository = Mock()
    handler = FirePlayerCommandHandler(
        game_repository,
        club_provider,
        contract_repository,
    )

    result = handler(FirePlayerCommand(
        game_id="missing-game",
        club_id="club",
        player_id="player",
    ))

    assert not result.success
    assert result.message == "Game not found"
    game_repository.save_game.assert_not_called()
    club_provider.save_club.assert_not_called()
    contract_repository.terminate_player_contracts.assert_not_called()
