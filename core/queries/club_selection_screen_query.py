"""
Created December 29, 2025

@author montreal91
"""
from typing import List
from typing import NamedTuple

from core.ports.outbound.temporal_club_provider import TemporalClubProvider


class ClubSelectionScreenQuery(NamedTuple):
    game_id: str


class ClubInfo(NamedTuple):
    club_name: str
    club_id: str


class ClubSelectionScreenQueryResult(NamedTuple):
    club_infos: List[ClubInfo]


class ClubSelectionScreenQueryHandler:
    def __init__(self, club_provider: TemporalClubProvider):
        self._club_provider = club_provider

    def __call__(self, query):
        clubs = self._club_provider.get_clubs_for_game(query.game_id).values()
        club_infos = []

        for club in clubs:
            club_infos.append(ClubInfo(club_name=club.name, club_id=club.club_id))

        return ClubSelectionScreenQueryResult(club_infos=club_infos)
