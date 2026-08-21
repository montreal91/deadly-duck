"""
Created August 20, 2026

@author montreal91
"""
from configuration.config_game import GameplayConstants
from core.club import Club
from core.player import level_exp
from core.player import Player
from core.skill_upgrade_system import upgrade_skills


def test_non_controlled_club_spends_player_skill_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club("ai_club", player)

    upgrade_skills(
        clubs={club.club_id: club},
        manager_club_id="manager_club",
    )

    assert player.skill_points == 0
    assert player.technique == 50
    assert player.endurance == 40 + _skill_growth_per_point()


def test_manager_club_keeps_unspent_player_skill_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club("manager_club", player)

    upgrade_skills(
        clubs={club.club_id: club},
        manager_club_id=club.club_id,
    )

    assert player.skill_points == 1
    assert player.technique == 50
    assert player.endurance == 40


def test_non_controlled_club_spends_all_player_skill_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1) + level_exp(2))
    club = _make_club("ai_club", player)

    upgrade_skills(
        clubs={club.club_id: club},
        manager_club_id=None,
    )

    assert player.skill_points == 0
    assert player.technique == 50
    assert player.endurance == 40 + 2 * _skill_growth_per_point()


def _make_club(club_id, player):
    club = Club(
        club_id=club_id,
        game_id="game",
        name=club_id,
        coach_power=1,
    )
    club.add_player(player)
    return club


def _skill_growth_per_point():
    return GameplayConstants.SKILL_GROWTH_PER_POINT.value
