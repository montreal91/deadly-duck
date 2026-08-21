"""
Created August 20, 2026

@author montreal91
"""
from typing import Dict
from typing import NamedTuple

from core.player import SkillSet

_SKILL_MAP = {
    "technique": SkillSet.TECHNIQUE,
    "endurance": SkillSet.ENDURANCE,
}


class ImprovePlayerSkillCommand(NamedTuple):
    game_id: str
    club_id: str
    player_id: str
    skill_points: Dict[str, int]


class ImprovePlayerSkillCommandResult(NamedTuple):
    success: bool
    message: str


class ImprovePlayerSkillCommandHandler:
    def __init__(self, game_repository, club_provider):
        self._game_repository = game_repository
        self._club_provider = club_provider

    def __call__(
            self,
            command: ImprovePlayerSkillCommand,
    ) -> ImprovePlayerSkillCommandResult:
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message=f"Game with id={command.game_id} not found.",
            )

        club = game.clubs.get(command.club_id)

        if club is None:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Incorrect club id.",
            )

        player_slot = club.get_player_slot(command.player_id)

        if player_slot is None:
            return ImprovePlayerSkillCommandResult(
                success=False,
                message="Incorrect player id.",
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
        player = player_slot.player

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

        self._game_repository.save_game(game)
        self._club_provider.save_clubs(game.clubs.values())

        return ImprovePlayerSkillCommandResult(success=True, message="OK")
