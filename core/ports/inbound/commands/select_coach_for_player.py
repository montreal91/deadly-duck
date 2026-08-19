"""
Created August 17, 2026

@author montreal91
"""
from typing import NamedTuple


class SelectCoachForPlayerCommand(NamedTuple):
    game_id: str
    club_id: str
    player_id: str
    coach_index: int


class SelectCoachForPlayerCommandResult(NamedTuple):
    success: bool
    message: str


class SelectCoachForPlayerCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(
            self,
            command: SelectCoachForPlayerCommand
    ) -> SelectCoachForPlayerCommandResult:
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return SelectCoachForPlayerCommandResult(
                success=False,
                message=f"Game with id={command.game_id} not found",
            )

        game.select_coach_for_player(
            coach_index=command.coach_index,
            player_id=command.player_id,
            club_index=command.club_id,
        )
        self._game_repository.save_game(game)

        return SelectCoachForPlayerCommandResult(success=True, message="")
