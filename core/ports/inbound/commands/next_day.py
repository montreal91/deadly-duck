"""
Created December 30, 2025

@author montreal91
"""
from dataclasses import dataclass
from typing import Optional

from core.game import Game
from core.ports.outbound.competition_repository import CompetitionRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class NextDayCommand:
    game_id: str

@dataclass(frozen=True)
class NextDayCommandResult:
    success: bool
    reason: str


class NextDayCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_repository: TemporalClubProvider,
            competition_repository: CompetitionRepository,
    ):
        self._game_repository = game_repository
        self._club_repository = club_repository
        self._competition_repository = competition_repository

    def __call__(self, command: NextDayCommand) -> NextDayCommandResult:
        game: Optional[Game] = self._game_repository.get_game(command.game_id)

        if game is None:
            return NextDayCommandResult(
                success=False,
                reason=f"Game with id={command.game_id} not found"
            )

        clubs = self._club_repository.get_clubs_for_game(command.game_id)

        res, reason = game.update(clubs)
        self._game_repository.save_game(game)
        self._club_repository.save_clubs(clubs.values())

        return NextDayCommandResult(success=res, reason=reason)
