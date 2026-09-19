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


def test_roster_management_query_returns_main_and_farm_rosters_without_context(
        tmp_path,
):
    game, clubs, conn = make_persisted_game(
        "roster-management-test",
        tmp_path / "game.sqlite",
    )
    master_club = next(
        club
        for club in clubs.values()
        if club.league_id == "master_league"
    )
    farm_club = clubs[master_club.farm_club_id]
    main_player_id = master_club.players[0].player.player_id
    second_main_player = master_club.players[1].player
    farm_player_id = farm_club.players[0].player.player_id
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
    assert [player.player_id for player in result.main_roster] == [
        player.player_id
        for player in sorted(
            [master_club.players[0].player, second_main_player],
            key=lambda player: player.level,
            reverse=True,
        )
    ]
    assert [player.player_id for player in result.farm_roster] == [farm_player_id]
    assert result.main_roster[0].contract_status == "Signed"
    assert result.farm_roster[0].contract_status == "Signed"
    game_repository.get_game.assert_not_called()
