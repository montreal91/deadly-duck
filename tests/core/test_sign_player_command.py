"""
Created September 18, 2026

@author montreal91

Tests for signing a player for the next season.
"""

from unittest.mock import Mock

from core.ports.inbound.commands.sign_player import SignPlayerCommand
from core.ports.inbound.commands.sign_player import SignPlayerCommandHandler
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.player_repository import PlayerRepository
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
    game._manager_club_id = club_id
    game_repository.save_game(game)
    player_id = club.players[0].player.player_id
    initial_balance = club.account.balance
    handler = SignPlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        make_game_params(),
        ContractRepository(conn),
    )

    result = handler(SignPlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    persisted_contract = conn.execute(
        """
        SELECT club_id, player_id, season_index, contract_cost, status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    ).fetchone()
    persisted_balance = conn.execute(
        """
        SELECT balance
        FROM club
        WHERE game_id = ? AND club_id = ?
        """,
        ("game", club_id),
    ).fetchone()[0]
    assert result.success
    assert tuple(persisted_contract) == (
        club_id,
        player_id,
        game.season_index + 1,
        10_000,
        "future",
    )
    assert persisted_balance == initial_balance - 10_000


def test_sign_player_command_does_not_save_when_player_is_already_signed(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "already-signed-player.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    game._manager_club_id = club_id
    game_repository.save_game(game)
    player_id = clubs[club_id].players[0].player.player_id
    ContractRepository(conn).create_future_contract(
        "game", club_id, player_id, game.season_index + 1, 10_000,
    )
    club_provider = Mock(wraps=TemporalClubProvider.get_instance())
    handler = SignPlayerCommandHandler(
        game_repository,
        club_provider,
        make_game_params(),
        ContractRepository(conn),
    )

    result = handler(SignPlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
    ))

    assert not result.success
    assert result.message == "This player already has a contract for the next season."
    club_provider.save_club.assert_not_called()


def test_signing_farm_player_creates_contract_for_controlled_master_club(
        tmp_path,
):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "sign-farm-player.sqlite",
    )
    master_club = clubs["darwin_ducks"]
    farm_club = clubs[master_club.farm_club_id]
    player_id = _eligible_player_id(master_club)
    PlayerAssignmentRepository(conn).assign_player(
        game.game_id,
        farm_club.club_id,
        player_id,
    )
    game._manager_club_id = master_club.club_id
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    handler = SignPlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        make_game_params(),
        ContractRepository(conn),
    )

    result = handler(SignPlayerCommand(
        game_id=game.game_id,
        club_id=farm_club.club_id,
        player_id=player_id,
    ))

    contract = conn.execute(
        '''
        SELECT club_id, player_id, season_index, contract_cost, status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        ''',
        (game.game_id, player_id),
    ).fetchone()
    assert result.success
    assert tuple(contract) == (
        master_club.club_id,
        player_id,
        game.season_index + 1,
        10_000,
        "future",
    )
    reloaded_farm_club = TemporalClubProvider.get_instance().get_clubs_for_game(
        game.game_id,
    )[farm_club.club_id]
    reloaded_player_slot = reloaded_farm_club.get_player_slot(player_id)
    player_info = PlayerRepository(conn).get_player_with_roster_info(
        game.game_id,
        player_id,
    )
    assert reloaded_player_slot is not None
    assert player_info is not None
    assert reloaded_player_slot.has_next_contract
    assert player_info.has_next_contract


def test_signing_player_from_other_organization_farm_club_is_rejected(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "sign-other-farm-player.sqlite",
    )
    controlled_master = clubs["darwin_ducks"]
    other_master = clubs["auckland_aces"]
    other_farm_club = clubs[other_master.farm_club_id]
    player_id = _eligible_player_id(other_master)
    PlayerAssignmentRepository(conn).assign_player(
        game.game_id,
        other_farm_club.club_id,
        player_id,
    )
    game._manager_club_id = controlled_master.club_id
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    handler = SignPlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        make_game_params(),
        ContractRepository(conn),
    )

    result = handler(SignPlayerCommand(
        game_id=game.game_id,
        club_id=other_farm_club.club_id,
        player_id=player_id,
    ))

    contract_count = conn.execute(
        '''
        SELECT COUNT(*)
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        ''',
        (game.game_id, player_id),
    ).fetchone()[0]
    assert not result.success
    assert contract_count == 0


def test_activating_next_season_contract_terminates_current_contract(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "activate-contract.sqlite",
    )
    club = clubs["darwin_ducks"]
    player_id = _eligible_player_id(club)
    contracts = ContractRepository(conn)
    contracts.create_active_contract(
        game.game_id,
        club.club_id,
        player_id,
        game.season_index,
        10_000,
    )
    contracts.create_future_contract(
        game.game_id,
        club.club_id,
        player_id,
        game.season_index + 1,
        12_000,
    )

    contracts.activate_future_contracts(game.game_id, game.season_index + 1)

    statuses = conn.execute(
        '''
        SELECT season_index, status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        ORDER BY season_index
        ''',
        (game.game_id, player_id),
    ).fetchall()
    assert [tuple(status) for status in statuses] == [
        (game.season_index, "terminated"),
        (game.season_index + 1, "active"),
    ]


def _eligible_player_id(club):
    return next(
        slot.player.player_id
        for slot in club.players
        if slot.player.age < 20
    )
