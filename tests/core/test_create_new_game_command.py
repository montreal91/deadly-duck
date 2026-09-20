"""
Created September 19, 2026

@author montreal91

Tests for creating a game and selecting its managed club.
"""

import sqlite3
from unittest.mock import Mock

from core.club import Club
from core.game import Game
from core.ports.inbound.commands.create_new_game import CreateNewGameCommand
from core.ports.inbound.commands.create_new_game import CreateNewGameCommandHandler
from core.ports.inbound.commands.select_club import SelectClubCommand
from core.ports.inbound.commands.select_club import SelectClubCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.player_repository import PlayerRepository
from core.ports.outbound.player_assignment_repository import PlayerAssignmentRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.queries.roster_management_screen_query import RosterManagementScreenQuery
from core.queries.roster_management_screen_query import (
    RosterManagementScreenQueryHandler,
)
from persistence.migration_history import init_db
from tests.core.fixtures.clubs import INITIAL_CLUBS
from tests.core.fixtures.game import make_game_params


def test_regular_championships_are_created_for_master_and_apprentice_leagues(
        monkeypatch,
):
    competition_repository = Mock()
    match_repository = Mock()
    monkeypatch.setattr(
        CompetitionRepository,
        "tmp_get_instance",
        staticmethod(lambda: competition_repository),
    )
    monkeypatch.setattr(
        ScheduledMatchRepository,
        "tmp_get_instance",
        staticmethod(lambda: match_repository),
    )
    game = Game.__new__(Game)
    game._game_id = "game"
    game._params = make_game_params()
    game._season_index = 0
    clubs = {
        club.club_id: club
        for club in (
            Club("master-one", "game", "Master One", 1, "master_league"),
            Club("master-two", "game", "Master Two", 1, "master_league"),
            Club("apprentice-one", "game", "Apprentice One", 1, "apprentice_league"),
            Club("apprentice-two", "game", "Apprentice Two", 1, "apprentice_league"),
        )
    }

    game._start_regular_championship(clubs)

    competitions = [
        call.kwargs["competition"]
        for call in competition_repository.save_competition.call_args_list
    ]
    assert len(competitions) == 2
    assert {frozenset(competition._club_ids) for competition in competitions} == {
        frozenset({"master-one", "master-two"}),
        frozenset({"apprentice-one", "apprentice-two"}),
    }


def test_create_game_then_select_club_persists_all_initial_clubs(tmp_path):
    db_path = tmp_path / "new-game.sqlite"
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    CompetitionRepository.tmp_initialize(conn)
    ScheduledMatchRepository.tmp_init(conn)
    MatchResultRepository.tmp_init(conn)
    PlayerRepository.tmp_init(conn)
    TemporalClubProvider.initialize(conn)

    game_id = "new-game"
    game_repository = GameRepository(conn)
    club_provider = TemporalClubProvider.get_instance()
    create_game = CreateNewGameCommandHandler(
        game_repository,
        make_game_params(),
        club_provider,
        PlayerAssignmentRepository(conn),
        contract_repository=ContractRepository(conn),
    )

    create_result = create_game(CreateNewGameCommand(game_id))
    clubs = club_provider.get_clubs_for_game(game_id)
    competitions = CompetitionRepository.tmp_get_instance().get_ongoing_competitions(
        game_id,
    )
    managed_club_id = next(iter(clubs))
    select_club = SelectClubCommandHandler(game_repository, club_provider)

    select_result = select_club(SelectClubCommand(
        game_id=game_id,
        club_id=managed_club_id,
    ))

    persisted_game = game_repository.get_game(game_id)

    assert persisted_game is not None

    persisted_clubs = club_provider.get_clubs_for_game(game_id)

    assert create_result.game_id == game_id
    assert select_result.success
    assert persisted_game.manager_club_id == managed_club_id
    master_competition = next(
        competition
        for competition in competitions
        if competition.contains_club("auckland_aces")
    )
    apprentice_competition = next(
        competition
        for competition in competitions
        if competition.contains_club("farm_club_0")
    )

    assert len(competitions) == 2
    assert all(
        master_competition.contains_club(club.club_id)
        for club in clubs.values()
        if club.league_id == "master_league"
    )
    assert not any(
        master_competition.contains_club(club.club_id)
        for club in clubs.values()
        if club.league_id == "apprentice_league"
    )
    assert all(
        apprentice_competition.contains_club(club.club_id)
        for club in clubs.values()
        if club.league_id == "apprentice_league"
    )
    assert set(persisted_clubs) == {
        club.club_id for club in INITIAL_CLUBS
    }

    roster_result = RosterManagementScreenQueryHandler(
        game_repository,
        club_provider,
        PlayerAssignmentRepository(conn),
    )(RosterManagementScreenQuery(
        game_id=game_id,
        manager_club_id="auckland_aces",
    ))

    assert roster_result.success
    assert roster_result.main_roster
    assert roster_result.farm_roster
    assert all(
        player.contract_status == "Signed"
        for player in roster_result.main_roster
    )
    assert all(
        player.contract_status == "Not Signed"
        for player in roster_result.farm_roster
    )

    for expected_club in INITIAL_CLUBS:
        persisted_club = persisted_clubs[expected_club.club_id]

        assert persisted_club.game_id == game_id
        assert persisted_club.name == expected_club.name
        assert persisted_club.coach_power == expected_club.coach_power
        assert persisted_club.account.balance == expected_club.balance
        assert len(persisted_club.players) == expected_club.player_count
        future_contract_count = conn.execute(
            '''
            SELECT COUNT(*)
            FROM "contract"
            WHERE game_id = ?
              AND club_id = ?
              AND season_index = ?
              AND status = 'future'
            ''',
            (game_id, expected_club.club_id, persisted_game.season_index + 1),
        ).fetchone()[0]
        assert future_contract_count == expected_club.contracted_player_count
