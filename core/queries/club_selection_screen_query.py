"""
Created December 29, 2025

@author montreal91
"""
from typing import List
from typing import NamedTuple

from core.club_data import load_club_info_by_id
from core.ports.outbound.temporal_club_provider import TemporalClubProvider


class ClubSelectionScreenQuery(NamedTuple):
    game_id: str


class ClubInfo(NamedTuple):
    club_name: str
    club_id: str
    country: str
    city: str
    motto: str
    description: str


class ClubSelectionScreenQueryResult(NamedTuple):
    club_infos: List[ClubInfo]


class ClubSelectionScreenQueryHandler:
    def __init__(self, club_provider: TemporalClubProvider):
        self._club_provider = club_provider

    def __call__(self, query):
        clubs = self._club_provider.get_clubs_for_game(query.game_id).values()
        club_info_by_id = load_club_info_by_id(club.club_id for club in clubs)
        club_infos = []

        for club in clubs:
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
