"""
Created August 20, 2026

@author montreal91
"""
from dataclasses import dataclass
from typing import Dict

from core.player import SkillSet
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.player_repository import PlayerRepository

_SKILL_MAP = {
    "technique": SkillSet.TECHNIQUE,
    "endurance": SkillSet.ENDURANCE,
}


@dataclass(frozen=True)
class ImprovePlayerSkillCommand:
    game_id: str
    club_id: str
    player_id: str
    skill_points: Dict[str, int]


@dataclass(frozen=True)
class ImprovePlayerSkillCommandResult:
    success: bool
    message: str


class ImprovePlayerSkillCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            player_repository: PlayerRepository,
    ):
        self._game_repository = game_repository
        self._player_repository = player_repository

    def __call__(
            self,
            command: ImprovePlayerSkillCommand,
    ) -> ImprovePlayerSkillCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return ImprovePlayerSkillCommandResult(
                success=False,
                message=f"Game with id={command.game_id} not found.",
            )

        invalid_keys = [
            key
            for key in command.skill_points
            if key not in _SKILL_MAP
        ]

        if invalid_keys:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Unknown skill.",
            )

        negative_values = [
            value
            for value in command.skill_points.values()
            if value < 0
        ]

        if negative_values:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Skill points cannot be negative.",
            )

        points_to_spend = sum(command.skill_points.values())
        roster_info = self._player_repository.get_player_with_roster_info(
            command.game_id,
            command.player_id
        )

        if roster_info is None:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Player not found.",
            )

        if roster_info.club_id != command.club_id:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Incorrect player id.",
            )

        player = roster_info.player

        if points_to_spend > player.skill_points:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Not enough skill points.",
            )

        for skill, points in command.skill_points.items():
            player.improve_skill(
                skill_points=points,
                skill=_SKILL_MAP[skill],
            )

        self._player_repository.save_player(player)
        return ImprovePlayerSkillCommandResult(success=True, message="OK")
