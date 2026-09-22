"""Tests for the roster management screen query."""

from unittest.mock import Mock

from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.queries.roster_management_screen_query import RosterManagementScreenQuery
from core.queries.roster_management_screen_query import (
    RosterManagementScreenQueryHandler,
)
from tests.core.fixtures.game import make_persisted_game


def test_roster_management_query_shows_active_only_contracts_as_not_signed(
        tmp_path,
):
    game, clubs, conn = make_persisted_game(
        "roster-management-test",
        tmp_path / "game.sqlite",
    )
    master_club = clubs["darwin_ducks"]
    farm_club = clubs[master_club.farm_club_id]
    main_player_id = master_club.players[0].player.player_id
    second_main_player = master_club.players[1].player
    farm_player_id = master_club.players[2].player.player_id
    assignments = PlayerAssignmentRepository(conn)
    contracts = ContractRepository(conn)
    assignments.assign_player(game.game_id, master_club.club_id, main_player_id)
    assignments.assign_player(
        game.game_id,
        master_club.club_id,
        second_main_player.player_id,
    )
    assignments.assign_player(game.game_id, farm_club.club_id, farm_player_id)
    contracts.create_active_contract(
        game.game_id,
        master_club.club_id,
        main_player_id,
        game.season_index,
        10_000,
    )
    contracts.create_active_contract(
        game.game_id,
        master_club.club_id,
        second_main_player.player_id,
        game.season_index,
        10_000,
    )
    contracts.create_active_contract(
        game.game_id,
        master_club.club_id,
        farm_player_id,
        game.season_index,
        10_000,
    )
    game_repository = Mock()
    game_repository.does_game_exist.return_value = True
    game_repository.get_game.side_effect = AssertionError(
        "Roster management must not read Game.get_context()."
    )
    handler = RosterManagementScreenQueryHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        assignments,
    )

    result = handler(RosterManagementScreenQuery(
        game_id=game.game_id,
        manager_club_id=master_club.club_id,
    ))

    assert result.success
    assert result.balance == master_club.account.balance
    assert result.farm_club_id == farm_club.club_id
    assert result.farm_club_name == farm_club.name
    expected_main_players = [
        slot.player
        for slot in master_club.players
        if slot.player.player_id != farm_player_id
    ]
    assert len(expected_main_players) > 0
    expected_farm_players = [
        *(slot.player for slot in farm_club.players),
        master_club.players[2].player,
    ]
    assert [player.player_id for player in result.main_roster] == [
        player.player_id
        for player in sorted(
            expected_main_players,
            key=lambda player: (
                -player.experience,
                player.first_name,
                player.last_name,
            ),
        )
    ]
    assert [player.player_id for player in result.farm_roster] == [
        player.player_id
        for player in sorted(
            expected_farm_players,
            key=lambda player: (
                -player.experience,
                player.first_name,
                player.last_name,
            ),
        )
    ]
    # An active contract covers the current season.  It must not be presented
    # as a next-season contract in the roster screen.
    assert result.main_roster[0].contract_status == "Not Signed"
    assert result.farm_roster[0].contract_status == "Not Signed"
    game_repository.get_game.assert_not_called()


def test_roster_management_query_shows_future_contracts_as_signed(
        tmp_path,
):
    game, clubs, conn = make_persisted_game(
        "roster-management-future-contracts-test",
        tmp_path / "game.sqlite",
    )
    master_club = clubs["darwin_ducks"]
    farm_club = clubs[master_club.farm_club_id]
    main_player_id = master_club.players[0].player.player_id
    farm_player_id = master_club.players[1].player.player_id
    assignments = PlayerAssignmentRepository(conn)
    assignments.assign_player(game.game_id, master_club.club_id, main_player_id)
    assignments.assign_player(game.game_id, farm_club.club_id, farm_player_id)
    _create_contract(
        conn,
        game.game_id,
        master_club.club_id,
        main_player_id,
        game.season_index + 1,
        12_000,
        "future",
    )
    _create_contract(
        conn,
        game.game_id,
        farm_club.club_id,
        farm_player_id,
        game.season_index + 1,
        9_000,
        "future",
    )
    game_repository = Mock()
    game_repository.does_game_exist.return_value = True
    handler = RosterManagementScreenQueryHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
        assignments,
    )

    result = handler(RosterManagementScreenQuery(
        game_id=game.game_id,
        manager_club_id=master_club.club_id,
    ))

    assert result.success
    assert result.main_roster[0].contract_status == "Signed"
    assert result.main_roster[0].contract_cost is None
    assert result.farm_roster[0].contract_status == "Signed"
    assert result.farm_roster[0].contract_cost is None


def _create_contract(
        conn,
        game_id,
        club_id,
        player_id,
        season_index,
        contract_cost,
        status,
):
    with conn:
        conn.execute(
            '''
            INSERT INTO "contract" (
                game_id,
                club_id,
                player_id,
                season_index,
                contract_cost,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                game_id,
                club_id,
                player_id,
                season_index,
                contract_cost,
                status,
            ),
        )
