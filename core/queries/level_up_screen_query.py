"""
Created August 20, 2026

@author montreal91
"""
from dataclasses import dataclass
from typing import List
from typing import Optional

from configuration.config_game import GameplayConstants
from core.player import Player
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


@dataclass(frozen=True)
class LevelUpScreenQuery:
    game_id: str
    club_id: str


@dataclass(frozen=True)
class LevelUpPlayer:
    player_id: str
    full_name: str
    level: int
    technique: int
    endurance: int
    available_skill_points: int
    club_name: str


@dataclass(frozen=True)
class LevelUpScreenQueryResult:
    players: List[LevelUpPlayer]
    skill_growth_per_point: int


class LevelUpScreenQueryHandler:
    # TODO: use player repository instead of temporal club provider
    def __init__(self, club_provider: TemporalClubProvider):
        self._club_provider = club_provider

    def __call__(
            self,
            query: LevelUpScreenQuery,
    ) -> LevelUpScreenQueryResult:
        clubs = self._club_provider.get_clubs_for_game(query.game_id)
        club = clubs.get(query.club_id)

        if club is None:
            return LevelUpScreenQueryResult(
                players=[],
                skill_growth_per_point=0
            )

        farm_club = clubs.get(club.farm_club_id or "")

        fc_players = farm_club.players if farm_club else []

        players = [
            _to_level_up_player(slot.player, club.name)
            for slot in club.players
            if _has_unspent_skill_points(slot.player)
        ]

        if farm_club is not None:
            players.extend(
                _to_level_up_player(slot.player, farm_club.name)
                for slot in fc_players
                if _has_unspent_skill_points(slot.player)
            )

        return LevelUpScreenQueryResult(
            players=players,
            skill_growth_per_point=GameplayConstants.SKILL_GROWTH_PER_POINT.value
        )


def _to_level_up_player(player: Optional[Player], club_name: str) -> LevelUpPlayer:
    if player is None:
        return LevelUpPlayer(
            player_id="",
            full_name="",
            level=0,
            technique=0,
            endurance=0,
            available_skill_points=0,
            club_name="",
        )

    return LevelUpPlayer(
        player_id=player.player_id,
        full_name=player.full_name,
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        available_skill_points=player.skill_points,
        club_name=club_name,
    )


def _has_unspent_skill_points(player: Optional[Player]) -> bool:
    return player is not None and player.skill_points > 0
