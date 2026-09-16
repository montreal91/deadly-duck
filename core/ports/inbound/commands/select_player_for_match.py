"""
Created August 19, 2026

@author montreal91
"""
from typing import NamedTuple
from typing import Optional


_CLUB_ID_ERROR = "Incorrect club id."
_PLAYER_ID_ERROR = "Incorrect player index."


class SelectPlayerForMatchCommand(NamedTuple):
    game_id: str
    club_id: str
    player_id: Optional[str]


class SelectPlayerForMatchCommandResult(NamedTuple):
    success: bool
    message: str


class SelectPlayerForMatchCommandHandler:
    def __init__(self, game_repository, club_provider):
        self._game_repository = game_repository
        self._club_provider = club_provider

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

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        assert command.club_id in clubs, _CLUB_ID_ERROR

        club = clubs[command.club_id]
        assert club.has_player(command.player_id), _PLAYER_ID_ERROR

        club.select_player(command.player_id)
        self._club_provider.save_club(club)

        return SelectPlayerForMatchCommandResult(success=True, message="OK")
