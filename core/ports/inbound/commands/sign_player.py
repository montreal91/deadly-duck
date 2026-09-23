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
            contract_repository,
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._contract_calculator = DdStaticContractCalculator(
            game_parameters.contracts
        )
        self._contract_repository = contract_repository

    def __call__(self, command: SignPlayerCommand) -> SignPlayerCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return SignPlayerCommandResult(False, "Game not found.")

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        game = self._game_repository.get_game(command.game_id)
        if game is None:
            return SignPlayerCommandResult(False, "Game not found.")

        master_club = clubs.get(game.manager_club_id)
        player_club = clubs.get(command.club_id)
        if not _is_player_club_in_managed_organization(
                master_club,
                player_club,
        ):
            return SignPlayerCommandResult(False, _CLUB_ID_ERROR)

        player_slot = player_club.get_player_slot(command.player_id)
        if player_slot is None:
            return SignPlayerCommandResult(False, "Incorrect player id.")

        if _has_next_season_contract(
                self._contract_repository,
                command,
        ):
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
        if master_club.account.balance < cost:
            return SignPlayerCommandResult(
                False,
                f"Insufficient funds.\nYou need at least ${cost}.",
            )

        master_club.account.ProcessTransaction(DdTransaction(
            -cost,
            f"Renewed player contract with {player.initials} ",
        ))
        self._club_provider.save_club(master_club)
        self._contract_repository.create_future_contract(
            game_id=command.game_id,
            club_id=master_club.club_id,
            player_id=command.player_id,
            season_index=game.season_index + 1,
            contract_cost=cost,
        )

        return SignPlayerCommandResult(success=True, message="Ok")


def _is_player_club_in_managed_organization(master_club, player_club) -> bool:
    if master_club is None or player_club is None:
        return False

    return player_club.club_id in {
        master_club.club_id,
        master_club.farm_club_id,
    }


def _has_next_season_contract(contract_repository, command) -> bool:
    return contract_repository.has_future_contract(
        command.game_id,
        command.player_id,
    )
