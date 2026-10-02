"""
Created August 20, 2026

@author montreal91
"""
from typing import Dict
from typing import Optional

from core.club import Club
from core.player import Player
from core.player import SkillSet


def upgrade_skills(
        clubs: Dict[str, Club],
        manager_club_id: Optional[str],
):
    farm_club_id = _get_manager_farm_club_id(clubs, manager_club_id)
    for club in clubs.values():
        if club.club_id == manager_club_id or club.club_id == farm_club_id:
            continue
        _upgrade_club_skills(club)


def _choose_skill_to_improve(player: Player) -> SkillSet:
    if player.technique <= player.endurance:
        return SkillSet.TECHNIQUE
    return SkillSet.ENDURANCE


def _upgrade_player_skills(player: Optional[Player]):
    if player is None:
        return

    while player.skill_points > 0:
        player.improve_skill(
            skill_points=1,
            skill=_choose_skill_to_improve(player),
        )


def _upgrade_club_skills(club: Club):
    for slot in club.players:
        _upgrade_player_skills(slot.player)


def _get_manager_farm_club_id(clubs: Dict[str, Club], manager_club_id: Optional[str]) -> Optional[str]:
    if manager_club_id is None:
        return None

    return clubs[manager_club_id].farm_club_id
