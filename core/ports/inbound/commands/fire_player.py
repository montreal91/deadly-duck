"""
Created August 17, 2026

@author montreal91
"""
from dataclasses import dataclass
from typing import Optional

from core.club import Club
from core.ports.outbound.contract_repository import ContractRepository
from core.ports.outbound.game_repository import GameRepository
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class FirePlayerCommand:
    game_id: str
    club_id: str
    player_id: str


@dataclass(frozen=True)
class FirePlayerCommandResult:
    success: bool
    message: str


class FirePlayerCommandHandler:
    def __init__(
            self,
            game_repository: GameRepository,
            club_provider: TemporalClubProvider,
            contract_repository: ContractRepository,
    ):
        self._game_repository = game_repository
        self._club_provider = club_provider
        self._contract_repository = contract_repository

    def __call__(self, command: FirePlayerCommand) -> FirePlayerCommandResult:
        if not self._game_repository.does_game_exist(command.game_id):
            return FirePlayerCommandResult(success=False, message="Game not found")

        clubs = self._club_provider.get_clubs_for_game(command.game_id)
        game = self._game_repository.get_game(command.game_id)

        if game is None:
            return FirePlayerCommandResult(success=False, message="Game not found")

        master_club = clubs.get(game.manager_club_id)
        player_club = clubs.get(command.club_id)

        if player_club is None:
            return FirePlayerCommandResult(
                success=False,
                message=f"There is no club with id=[{command.club_id}]."
            )

        if not _is_player_club_in_managed_organization(
                master_club,
                player_club,
        ):
            return FirePlayerCommandResult(
                success=False,
                message="Incorrect club id.",
            )

        if not player_club.has_player(command.player_id):
            return FirePlayerCommandResult(
                success=False,
                message="There is no player with such id in your club.",
            )

        player = player_club.pop_player(command.player_id)
        player.recover_stamina(player.max_stamina)
        self._club_provider.save_club(player_club)
        self._contract_repository.terminate_player_contracts(
            command.game_id,
            command.player_id,
        )

        return FirePlayerCommandResult(success=True, message="")


def _is_player_club_in_managed_organization(
        master_club: Optional[Club],
        player_club: Optional[Club],
) -> bool:
    if master_club is None or player_club is None:
        return False

    return player_club.club_id in {
        master_club.club_id,
        master_club.farm_club_id,
    }
