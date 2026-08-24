"""
Created December 29, 2025

@author montreal91
"""
import json
from typing import List
from typing import NamedTuple

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
        self._club_info_by_id = _load_club_info_by_id()

    def __call__(self, query):
        clubs = self._club_provider.get_clubs_for_game(query.game_id).values()
        club_infos = []

        for club in clubs:
            info = self._club_info_by_id.get(club.club_id, _empty_info())
            club_infos.append(ClubInfo(
                club_name=club.name,
                club_id=club.club_id,
                country=info.country,
                city=info.city,
                motto=info.motto,
                description=info.description,
            ))

        return ClubSelectionScreenQueryResult(club_infos=club_infos)


class _StaticClubInfo(NamedTuple):
    country: str
    city: str
    motto: str
    description: str


def _load_club_info_by_id():
    with open("data/clubs.json", "r", encoding="utf-8") as data_file:
        raw_clubs = json.load(data_file)

    result = {}
    for club in raw_clubs:
        raw_info = club.get("info", {})
        result[club["club_id"]] = _StaticClubInfo(
            country=raw_info.get("country", "") or "",
            city=raw_info.get("city", "") or "",
            motto=raw_info.get("motto", "") or "",
            description=raw_info.get("description", "") or "",
        )
    return result


def _empty_info():
    return _StaticClubInfo(
        country="",
        city="",
        motto="",
        description="",
    )
