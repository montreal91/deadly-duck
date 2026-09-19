"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass

from configuration.config_game import GameplayConstants
from core.financial import DdStaticContractCalculator
from core.financial import DdTransaction
from core.game import GameParams
from core.player import PlayerFactory
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_CLUB_ID_ERROR = "Incorrect club id."


@dataclass(frozen=True)
class HireNewPlayerCommand:
    club_id: str
    game_id: str


@dataclass(frozen=True)
class HireNewPlayerCommandResult:
    success: bool
    message: str


class HireNewPlayerCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider: TemporalClubProvider,
            game_parameters: GameParams
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._contract_calculator = DdStaticContractCalculator(
            game_parameters.contracts
        )
        self._player_factory = PlayerFactory()

    def __call__(self, command: HireNewPlayerCommand) -> HireNewPlayerCommandResult:
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return HireNewPlayerCommandResult(
                success=False,
                message=f"Game with id {command.game_id} not found."
            )

        clubs = self._club_provider.get_clubs_for_game(command.game_id)

        if command.club_id not in clubs:
            return HireNewPlayerCommandResult(success=False, message=_CLUB_ID_ERROR)

        club = clubs[command.club_id]
        player = self._player_factory.create_player(
            level=0,
            age=GameplayConstants.STARTING_AGE.value,
        )

        cost = self._contract_calculator(player.level)

        if cost > club.account.balance:
            return HireNewPlayerCommandResult(
                success=False,
                message=f"Insufficient funds. You need at least ${cost}."
            )

        club.add_player(player)

        if game.manager_club_id == command.club_id:
            club.select_coach(coach_index=0, player_id=player.player_id)

        club.account.ProcessTransaction(DdTransaction(
            -cost,
            f"New player contract with {player.initials}.",
        ))
        self._club_provider.save_club(club)

        return HireNewPlayerCommandResult(success=True, message="OK")
