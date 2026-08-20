"""
Created August 20, 2026

@author montreal91
"""
from typing import List
from typing import NamedTuple

from configuration.config_game import GameplayConstants
from core.player import Player
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


class LevelUpScreenQuery(NamedTuple):
    game_id: str
    club_id: str


class LevelUpPlayer(NamedTuple):
    player_id: str
    full_name: str
    level: int
    technique: int
    endurance: int
    available_skill_points: int


class LevelUpScreenQueryResult(NamedTuple):
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

        players = [
            _to_level_up_player(slot.player)
            for slot in club.players
            if slot.player.skill_points > 0
        ]

        return LevelUpScreenQueryResult(
            players=players,
            skill_growth_per_point=GameplayConstants.SKILL_GROWTH_PER_POINT.value
        )


def _to_level_up_player(player: Player) -> LevelUpPlayer:
    return LevelUpPlayer(
        player_id=player.player_id,
        full_name=player.full_name,
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        available_skill_points=player.skill_points,
    )
