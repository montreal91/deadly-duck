"""
Created September 19, 2026

@author montreal91

Tests for the club selection screen query.
"""

from unittest.mock import Mock

from core.club import Club
from core.club_data import StaticClubInfo
from core.queries.club_selection_screen_query import ClubSelectionScreenQuery
from core.queries.club_selection_screen_query import ClubSelectionScreenQueryHandler


def test_club_selection_query_returns_only_master_league_clubs(monkeypatch):
    master_club = Club(
        "master-club",
        "game",
        "Master Club",
        1,
        league_id="master_league",
    )
    farm_club = Club(
        "farm-club",
        "game",
        "Farm Club",
        1,
        league_id="apprentice_league",
    )
    club_provider = Mock()
    club_provider.get_clubs_for_game.return_value = {
        master_club.club_id: master_club,
        farm_club.club_id: farm_club,
    }
    monkeypatch.setattr(
        "core.queries.club_selection_screen_query.load_club_info_by_id",
        lambda club_ids: {
            club_id: StaticClubInfo("Country", "City", "Motto", "Description")
            for club_id in club_ids
        },
    )
    handler = ClubSelectionScreenQueryHandler(club_provider)

    result = handler(ClubSelectionScreenQuery("game"))

    assert [club.club_id for club in result.club_infos] == ["master-club"]
