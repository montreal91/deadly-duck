"""
Created September 19, 2026

@author montreal91

Tests for creating a game and selecting its managed club.
"""

import sqlite3

from core.ports.inbound.commands.create_new_game import CreateNewGameCommand
from core.ports.inbound.commands.create_new_game import CreateNewGameCommandHandler
from core.ports.inbound.commands.select_club import SelectClubCommand
from core.ports.inbound.commands.select_club import SelectClubCommandHandler
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.match_result_repository import MatchResultRepository
from core.ports.outbound.player_repository import PlayerRepository
from core.ports.outbound.scheduled_match_repository import ScheduledMatchRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from persistence.migration_history import init_db
from tests.core.fixtures.clubs import INITIAL_CLUBS
from tests.core.fixtures.game import make_game_params


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
    )

    create_result = create_game(CreateNewGameCommand(game_id))
    clubs = club_provider.get_clubs_for_game(game_id)
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
    assert set(persisted_clubs) == {
        club.club_id for club in INITIAL_CLUBS
    }

    for expected_club in INITIAL_CLUBS:
        persisted_club = persisted_clubs[expected_club.club_id]

        assert persisted_club.game_id == game_id
        assert persisted_club.name == expected_club.name
        assert persisted_club.coach_power == expected_club.coach_power
        assert persisted_club.account.balance == expected_club.balance
        assert len(persisted_club.players) == expected_club.player_count
        assert sum(
            slot.has_next_contract for slot in persisted_club.players
        ) == expected_club.contracted_player_count
