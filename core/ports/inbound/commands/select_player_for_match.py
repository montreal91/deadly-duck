"""
Created August 19, 2026

@author montreal91
"""
from typing import NamedTuple
from typing import Optional


class SelectPlayerForMatchCommand(NamedTuple):
    game_id: str
    club_id: str
    player_id: Optional[str]


class SelectPlayerForMatchCommandResult(NamedTuple):
    success: bool
    message: str


class SelectPlayerForMatchCommandHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(
            self,
            command: SelectPlayerForMatchCommand
    ) -> SelectPlayerForMatchCommandResult:
        if command.player_id is None:
            return SelectPlayerForMatchCommandResult(
                success=False,
                message="Player id is required."
            )

        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return SelectPlayerForMatchCommandResult(
                success=False,
                message=f"Game with id=[{command.game_id} not found."
            )

        game.select_player(club_id=command.club_id, player_id=command.player_id)
        self._game_repository.save_game(game)

        return SelectPlayerForMatchCommandResult(success=True, message="OK")
