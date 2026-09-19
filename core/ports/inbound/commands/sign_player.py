"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass

from configuration.config_game import GameplayConstants
from core.financial import DdStaticContractCalculator
from core.financial import DdTransaction
from core.game import GameParams
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_CLUB_ID_ERROR = "Incorrect club id."


@dataclass(frozen=True)
class SignPlayerCommand:
    game_id: str
    club_id: str
    player_id: str


@dataclass(frozen=True)
class SignPlayerCommandResult:
    success: bool
    message: str


class SignPlayerCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider: TemporalClubProvider,
            game_parameters: GameParams,
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._contract_calculator = DdStaticContractCalculator(
            game_parameters.contracts
        )

    def __call__(self, command: SignPlayerCommand) -> SignPlayerCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return SignPlayerCommandResult(False, "Game not found.")

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        club = clubs.get(command.club_id)
        if club is None:
            return SignPlayerCommandResult(False, _CLUB_ID_ERROR)

        player_slot = club.get_player_slot(command.player_id)
        if player_slot is None:
            return SignPlayerCommandResult(False, "Incorrect player id.")

        if player_slot.has_next_contract:
            return SignPlayerCommandResult(
                False,
                "This player already has a contract for the next season.",
            )

        player = player_slot.player

        if player is None:
            raise RuntimeError("Player Roster Entry without Player.")

        if player.age + 1 >= GameplayConstants.RETIREMENT_AGE.value:
            return SignPlayerCommandResult(
                False,
                f"{player.initials} is too old to play next season.",
            )

        cost = self._contract_calculator(player.level)
        if club.account.balance < cost:
            return SignPlayerCommandResult(
                False,
                f"Insufficient funds.\nYou need at least ${cost}.",
            )

        club.contract_player(command.player_id)
        club.account.ProcessTransaction(DdTransaction(
            -cost,
            f"Renewed player contract with {player.initials} ",
        ))
        self._club_provider.save_club(club)

        return SignPlayerCommandResult(success=True, message="Ok")
