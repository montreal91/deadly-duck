"""
Created December 29, 2025

@author montreal91
"""
from dataclasses import dataclass
from typing import List

from core.club_data import load_club_info_by_id
from core.ports.outbound.temporal_club_provider import TemporalClubProvider

_MASTER_LEAGUE_ID = "master_league"


@dataclass(frozen=True)
class ClubSelectionScreenQuery:
    game_id: str


@dataclass(frozen=True)
class ClubInfo:
    club_name: str
    club_id: str
    country: str
    city: str
    motto: str
    description: str


@dataclass(frozen=True)
class ClubSelectionScreenQueryResult:
    club_infos: List[ClubInfo]


class ClubSelectionScreenQueryHandler:
    def __init__(self, club_provider: TemporalClubProvider):
        self._club_provider = club_provider

    def __call__(self, query):
        all_clubs = list(
            self._club_provider.get_clubs_for_game(query.game_id).values()
        )
        club_info_by_id = load_club_info_by_id(
            [club.club_id for club in all_clubs]
        )
        club_infos = []

        for club in all_clubs:
            if club.league_id != _MASTER_LEAGUE_ID:
                continue

            info = club_info_by_id[club.club_id]
            club_infos.append(ClubInfo(
                club_name=club.name,
                club_id=club.club_id,
                country=info.country,
                city=info.city,
                motto=info.motto,
                description=info.description,
            ))

        return ClubSelectionScreenQueryResult(club_infos=club_infos)
