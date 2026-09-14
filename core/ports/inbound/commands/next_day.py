"""
Created December 30, 2025

@author montreal91
"""
from typing import NamedTuple

from core.ports.outbound.temporal_club_provider import TemporalClubProvider


class NextDayCommand(NamedTuple):
    game_id: str


class NextDayCommandResult(NamedTuple):
    success: bool
    reason: str


class NextDayCommandHandler:
    def __init__(
            self,
            game_repository,
            club_repository: TemporalClubProvider,
            competition_repository=None,
    ):
        self._game_repository = game_repository
        self._club_repository = club_repository
        self._competition_repository = competition_repository

    def __call__(self, command):
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return NextDayCommandResult(
                success=False,
                reason=f"Game with id={command.game_id} not found"
            )

        previous_competition = game.competition
        previous_season_index = game.season_index
        res, reason = game.update()
        self._game_repository.save_game(game)
        self._club_repository.save_clubs(game.clubs.values())
        self._save_competitions(
            game,
            previous_competition,
            previous_season_index,
        )

        return NextDayCommandResult(success=res, reason=reason)

    def _save_competitions(
            self,
            game,
            previous_competition,
            previous_season_index: int,
    ):
        if self._competition_repository is None:
            return

        if previous_competition is not game.competition:
            self._competition_repository.save(
                game_id=game.game_id,
                competition=previous_competition,
                season_index=previous_season_index,
                is_current=False,
            )

        self._competition_repository.save(
            game_id=game.game_id,
            competition=game.competition,
            season_index=game.season_index,
        )
