"""Tests for assigning contracted players between a master club and its farm."""

import pytest

from core.ports.inbound.commands.assign_player import AssignPlayerCommand
from core.ports.inbound.commands.assign_player import AssignPlayerCommandHandler
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from tests.core.fixtures.game import make_persisted_game


def test_assign_player_promotes_from_farm_to_owning_master_club(tmp_path):
    game, master_club, farm_club, player_id, assignments, conn, handler = _setup(
        tmp_path,
    )
    assignments.assign_player(game.game_id, farm_club.club_id, player_id)
    contract_before = _contract(conn, game.game_id, player_id)

    result = handler(AssignPlayerCommand(
        game_id=game.game_id,
        master_club_id=master_club.club_id,
        target_club_id=master_club.club_id,
        player_id=player_id,
    ))

    assert result.success
    assert assignments.get_assigned_club_id(game.game_id, player_id) == master_club.club_id
    assert _contract(conn, game.game_id, player_id) == contract_before


def test_assign_player_demotes_from_master_to_own_farm_club(tmp_path):
    game, master_club, farm_club, player_id, assignments, conn, handler = _setup(
        tmp_path,
    )
    assignments.assign_player(game.game_id, master_club.club_id, player_id)
    contract_before = _contract(conn, game.game_id, player_id)

    result = handler(AssignPlayerCommand(
        game_id=game.game_id,
        master_club_id=master_club.club_id,
        target_club_id=farm_club.club_id,
        player_id=player_id,
    ))

    assert result.success
    assert assignments.get_assigned_club_id(game.game_id, player_id) == farm_club.club_id
    assert _contract(conn, game.game_id, player_id) == contract_before


@pytest.mark.parametrize("current_location,target_location", [
    ("other-master", "farm"),
    ("master", "master"),
    ("farm", "farm"),
])
def test_assign_player_rejects_invalid_assignment(
        tmp_path,
        current_location,
        target_location,
):
    game, master_club, farm_club, player_id, assignments, conn, handler = _setup(
        tmp_path,
    )
    clubs = TemporalClubProvider.get_instance().get_clubs_for_game(game.game_id)
    other_master_club = next(
        club
        for club in clubs.values()
        if club.league_id == "master_league"
        and club.club_id != master_club.club_id
    )
    locations = {
        "master": master_club.club_id,
        "farm": farm_club.club_id,
        "other-master": other_master_club.club_id,
    }
    assignments.assign_player(
        game.game_id,
        locations[current_location],
        player_id,
    )
    contract_before = _contract(conn, game.game_id, player_id)

    result = handler(AssignPlayerCommand(
        game_id=game.game_id,
        master_club_id=master_club.club_id,
        target_club_id=locations[target_location],
        player_id=player_id,
    ))

    assert not result.success
    assert assignments.get_assigned_club_id(
        game.game_id,
        player_id,
    ) == locations[current_location]
    assert _contract(conn, game.game_id, player_id) == contract_before


def _setup(tmp_path):
    game, clubs, conn = make_persisted_game(
        "assign-player-test",
        tmp_path / "game.sqlite",
    )
    master_club = next(
        club
        for club in clubs.values()
        if club.league_id == "master_league"
    )
    farm_club = clubs[master_club.farm_club_id]
    player_id = master_club.players[0].player.player_id
    assignments = PlayerAssignmentRepository(conn)
    ContractRepository(conn).create_active_contract(
        game_id=game.game_id,
        club_id=master_club.club_id,
        player_id=player_id,
        season_index=game.season_index,
        contract_cost=10_000,
    )
    handler = AssignPlayerCommandHandler(
        TemporalClubProvider.get_instance(),
        assignments,
    )
    return game, master_club, farm_club, player_id, assignments, conn, handler


def _contract(conn, game_id, player_id):
    row = conn.execute(
        """
        SELECT club_id, season_index, contract_cost, status
        FROM "contract"
        WHERE game_id = ? AND player_id = ?
        """,
        (game_id, player_id),
    ).fetchone()
    return tuple(row)
