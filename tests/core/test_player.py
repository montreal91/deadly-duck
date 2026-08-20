"""
Created August 20, 2026

@author montreal91
"""
from typing import cast

import pytest

from configuration.config_game import GameplayConstants
from core.player import level_exp
from core.player import Player
from core.player import SkillSet


def test_player_starts_with_no_skill_points():
    player = Player()

    assert player.skill_points == 0


def test_add_experience_below_next_level_does_not_add_skill_points():
    player = Player(technique=50, endurance=50)

    player.add_experience(player.next_level_exp - 1)

    assert player.level == 0
    assert player.skill_points == 0
    assert player.technique == 50
    assert player.endurance == 50


def test_add_experience_adds_skill_point_when_player_levels_up():
    player = Player()

    player.add_experience(player.next_level_exp)

    assert player.level == 1
    assert player.skill_points == _skill_points_per_level()


def test_add_experience_adds_skill_point_for_each_gained_level():
    player = Player()
    first_two_levels_exp = level_exp(1) + level_exp(2)

    player.add_experience(first_two_levels_exp)

    assert player.level == 2
    assert player.skill_points == 2 * _skill_points_per_level()


@pytest.mark.parametrize("experience", [0, 1, 25])
def test_add_experience_accumulates_experience(experience):
    player = Player()

    player.add_experience(experience)

    assert player.experience == experience


def test_improve_skill_spends_points_and_improves_technique():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))

    player.improve_skill(1, SkillSet.TECHNIQUE)

    assert player.technique == 50 + _skill_growth_per_level()
    assert player.endurance == 40
    assert player.skill_points == 0


def test_improve_skill_spends_points_and_improves_endurance():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))

    player.improve_skill(1, SkillSet.ENDURANCE)

    assert player.technique == 50
    assert player.endurance == 40 + _skill_growth_per_level()
    assert player.skill_points == 0


def test_improve_skill_can_spend_multiple_points_at_once():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1) + level_exp(2))

    player.improve_skill(2, SkillSet.TECHNIQUE)

    assert player.technique == 50 + 2 * _skill_growth_per_level()
    assert player.endurance == 40
    assert player.skill_points == 0


def test_improve_skill_does_nothing_when_spending_more_points_than_available():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))

    player.improve_skill(2, SkillSet.TECHNIQUE)

    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1


def _skill_points_per_level():
    return GameplayConstants.SKILL_POINTS_PER_LEVEL.value


def _skill_growth_per_level():
    return GameplayConstants.SKILL_GROWTH_PER_POINT.value


def test_improve_skill_does_nothing_when_spending_negative_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))

    player.improve_skill(-1, SkillSet.TECHNIQUE)

    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1


def test_improve_skill_does_nothing_when_spending_zero_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))

    player.improve_skill(0, SkillSet.TECHNIQUE)

    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1


def test_improve_skill_raises_for_unknown_skill():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    unknown_skill = cast(SkillSet, cast(object, "volley"))

    with pytest.raises(ValueError):
        player.improve_skill(1, unknown_skill)

    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
