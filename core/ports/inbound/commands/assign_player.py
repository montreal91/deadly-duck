"""
Created September 19, 2026

@author montreal91
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssignPlayerCommand:
    game_id: str
    master_club_id: str
    target_club_id: str
    player_id: str


@dataclass(frozen=True)
class AssignPlayerCommandResult:
    success: bool
    message: str = ""


class AssignPlayerCommandHandler:
    def __call__(self, command: AssignPlayerCommand) -> AssignPlayerCommandResult:
        return AssignPlayerCommandResult(True)
