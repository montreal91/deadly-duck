"""
Created Aug 20, 2026

@author montreal91
"""
from unittest.mock import Mock

from core.club import Club
from core.player import Player
from core.player import level_exp
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommand,
)
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommandHandler,
)
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.player_repository import PlayerRepository
from core.ports.outbound.player_repository import PlayerRosterInfo
from tests.core.fixtures.game import make_persisted_game


def test_improve_player_skill_command_persists_improved_player(tmp_path):
    game, clubs, conn = make_persisted_game(
        "game",
        tmp_path / "improve-player-skill.sqlite",
    )
    game_repository = GameRepository(conn)
    player_repository = PlayerRepository(conn)
    game_repository.save_game(game)
    club_id = next(iter(clubs))
    player = clubs[club_id].players[0].player
    initial_technique = player.technique
    conn.execute(
        """
        UPDATE player
        SET skill_points = 1
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player.player_id),
    )
    conn.commit()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id=club_id,
        player_id=player.player_id,
        skill_points={"technique": 1},
    ))

    persisted_player = conn.execute(
        """
        SELECT technique, skill_points
        FROM player
        WHERE game_id = ? AND player_id = ?
        """,
        ("game", player.player_id),
    ).fetchone()
    assert result.success
    assert tuple(persisted_player) == (initial_technique + 5, 0)


def test_improve_player_skill_command_rejects_missing_game():
    game_repository = _game_repository(None)
    club_provider = _club_provider()
    player_repository = _player_repository(None)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="missing-game",
        club_id="club",
        player_id="player",
        skill_points={"technique": 1},
    ))

    assert not result.success
    assert result.message == "Game with id=missing-game not found."
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_not_called()


def test_improve_player_skill_command_improves_player_and_saves_game():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1) + level_exp(2))
    club = _make_club(player)
    game = _game(clubs={"club": club})
    game_repository = _game_repository(game)
    club_provider = _club_provider()
    player_repository = _player_repository(player)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={
            "technique": 1,
            "endurance": 1,
        },
    ))

    assert result.success
    assert player.technique == 55
    assert player.endurance == 45
    assert player.skill_points == 0
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_called_once_with(player)


def test_improve_player_skill_command_rejects_invalid_skill_key():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _game_repository(_game(clubs={"club": club}))
    club_provider = _club_provider()
    player_repository = _player_repository(player)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"volley": 1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_not_called()


def test_improve_player_skill_command_rejects_negative_skill_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _game_repository(_game(clubs={"club": club}))
    club_provider = _club_provider()
    player_repository = _player_repository(player)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"technique": -1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_not_called()


def test_improve_player_skill_command_rejects_overspending():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _game_repository(_game(clubs={"club": club}))
    club_provider = _club_provider()
    player_repository = _player_repository(player)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"technique": 2},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_not_called()


def test_improve_player_skill_command_rejects_player_from_wrong_club():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    wrong_club = Club(
        club_id="wrong-club",
        game_id="game",
        name="Wrong Club",
        coach_power=1,
    )
    game_repository = _game_repository(_game(clubs={
        "club": club,
        "wrong-club": wrong_club,
    }))
    club_provider = _club_provider()
    player_repository = _player_repository(player)
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        player_repository,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="wrong-club",
        player_id=player.player_id,
        skill_points={"technique": 1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    game_repository.save_game.assert_not_called()
    club_provider.save_clubs.assert_not_called()
    player_repository.save_player.assert_not_called()


def _make_club(player):
    club = Club(
        club_id="club",
        game_id="game",
        name="Club",
        coach_power=1,
    )
    club.add_player(player)
    return club


def _game(clubs):
    game = Mock()
    game.clubs = clubs
    return game


def _game_repository(game):
    repository = Mock()
    repository.get_game.return_value = game
    repository.does_game_exist.return_value = game is not None
    return repository


def _club_provider():
    return Mock()


def _player_repository(player, club_id="club"):
    repository = Mock()
    repository.get_player_with_roster_info.return_value = (
        None
        if player is None
        else PlayerRosterInfo(
            player=player,
            club_id=club_id,
            club_name="Club",
            coach_level=0,
            contract_cost=0,
            has_next_contract=False,
        )
    )
    return repository
