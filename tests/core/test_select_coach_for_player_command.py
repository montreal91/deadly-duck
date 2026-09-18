"""
Created September 19, 2026

@author montreal91

Tests for assigning a coach to a roster player.
"""

from unittest.mock import Mock

from core.club import Club
from core.player import Player
from core.ports.inbound.commands.select_coach_for_player import (
    SelectCoachForPlayerCommand,
)
from core.ports.inbound.commands.select_coach_for_player import (
    SelectCoachForPlayerCommandHandler,
)
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from tests.core.fixtures.game import make_persisted_game


def test_select_coach_for_player_command_persists_coach_level(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "select-coach.sqlite",
    )
    game_repository = GameRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    player_id = clubs[club_id].players[0].player.player_id
    conn.execute(
        """
        UPDATE roster_entry
        SET coach_level = 0
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    )
    conn.commit()
    handler = SelectCoachForPlayerCommandHandler(
        game_repository,
        TemporalClubProvider.get_instance(),
    )

    result = handler(SelectCoachForPlayerCommand(
        game_id="game",
        club_id=club_id,
        player_id=player_id,
        coach_index=2,
    ))

    persisted_coach_level = conn.execute(
        """
        SELECT coach_level
        FROM roster_entry
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player_id),
    ).fetchone()[0]
    assert result.success
    assert persisted_coach_level == 2


def test_select_coach_for_player_command_rejects_missing_game_without_saving():
    game_repository = Mock()
    game_repository.does_game_exist.return_value = False
    club_provider = Mock()
    handler = SelectCoachForPlayerCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(SelectCoachForPlayerCommand(
        game_id="missing-game",
        club_id="club",
        player_id="player",
        coach_index=2,
    ))

    assert not result.success
    assert result.message == "Game with id=missing-game not found"
    game_repository.save_game.assert_not_called()
    club_provider.save_club.assert_not_called()


def test_select_coach_for_player_command_rejects_unknown_club():
    handler, club_provider = _handler_with_clubs({})

    result = handler(SelectCoachForPlayerCommand(
        game_id="game",
        club_id="missing-club",
        player_id="player",
        coach_index=2,
    ))

    assert not result.success
    assert result.message == "Incorrect club id."
    club_provider.save_club.assert_not_called()


def test_select_coach_for_player_command_rejects_unknown_player():
    club = _club()
    handler, club_provider = _handler_with_clubs({"club": club})

    result = handler(SelectCoachForPlayerCommand(
        game_id="game",
        club_id="club",
        player_id=str(Player().player_id),
        coach_index=2,
    ))

    assert not result.success
    assert result.message == "Incorrect player index."
    club_provider.save_club.assert_not_called()


def test_select_coach_for_player_command_rejects_invalid_coach_index():
    club = _club()
    player = Player()
    club.add_player(player)
    handler, club_provider = _handler_with_clubs({"club": club})

    result = handler(SelectCoachForPlayerCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        coach_index=4,
    ))

    assert not result.success
    assert result.message == "Incorrect coach index."
    club_provider.save_club.assert_not_called()


def _handler_with_clubs(clubs):
    game_repository = Mock()
    game_repository.does_game_exist.return_value = True
    club_provider = Mock()
    club_provider.get_clubs_for_game.return_value = clubs
    return (
        SelectCoachForPlayerCommandHandler(game_repository, club_provider),
        club_provider,
    )


def _club():
    return Club(
        club_id="club",
        game_id="game",
        name="Club",
        coach_power=1,
    )
