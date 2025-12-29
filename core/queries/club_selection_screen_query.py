"""
Created December 29, 2025

@author montreal91
"""
from typing import List
from typing import NamedTuple
from uuid import UUID


class ClubSelectionScreenQuery(NamedTuple):
    game_id: str


class ClubInfo(NamedTuple):
    club_name: str
    club_id: UUID


class ClubSelectionScreenQueryResult(NamedTuple):
    club_infos: List[ClubInfo]


class ClubSelectionScreenQueryHandler:
    def __init__(self, club_repository):
        self._club_repository = club_repository

    def __call__(self, query):
        clubs = self._club_repository.get_all_clubs(query.game_id)
        club_infos = []

        for club in clubs:
            club_infos.append(ClubInfo(club_name=club.name, club_id=club.club_id))

        return ClubSelectionScreenQueryResult(club_infos=club_infos)
