"""
Created August 20, 2026

@author montreal91
"""
from typing import NamedTuple
from typing import Optional

from core.ports.outbound.player_repository import PlayerRepository


class PlayerDetailsScreenQuery(NamedTuple):
    game_id: str
    player_id: str


class PlayerDetailsScreenQueryResult(NamedTuple):
    success: bool
    message: str
    player: Optional["PlayerDetailsInfo"]


class PlayerDetailsInfo(NamedTuple):
    player_id: str
    name: str
    age: int
    level: int
    experience: int
    next_level_experience: int
    technique: int
    endurance: int
    current_stamina: int
    max_stamina: int
    exhaustion: int
    club_name: str
    contract_status: str


class PlayerDetailsScreenQueryHandler:
    def __init__(self, player_repository: PlayerRepository):
        self._player_repository = player_repository

    def __call__(
            self,
            query: PlayerDetailsScreenQuery,
    ) -> PlayerDetailsScreenQueryResult:
        player_info = self._player_repository.get_player_with_roster_info(
            game_id=query.game_id,
            player_id=query.player_id,
        )

        if player_info is None:
            return PlayerDetailsScreenQueryResult(
                success=False,
                message=f"Player with id={query.player_id} not found",
                player=None,
            )

        return PlayerDetailsScreenQueryResult(
            success=True,
            message="Ok",
            player=_make_player_details_info(player_info),
        )


def _make_player_details_info(player_info) -> PlayerDetailsInfo:
    player = player_info.player
    return PlayerDetailsInfo(
        player_id=player.player_id,
        name=player.full_name,
        age=player.age,
        level=player.level,
        experience=player.experience,
        next_level_experience=player.next_level_exp,
        technique=player.technique,
        endurance=player.endurance,
        current_stamina=player.current_stamina,
        max_stamina=player.max_stamina,
        exhaustion=player.exhaustion,
        club_name=player_info.club_name or "Free Agent",
        contract_status=_contract_status(player_info.has_next_contract),
    )


def _contract_status(has_next_contract) -> str:
    if has_next_contract is None:
        return "N/A"
    if has_next_contract:
        return "Signed"
    return "Unsigned"
