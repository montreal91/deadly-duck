"""
Created Aug 20, 2026

@author montreal91
"""
from unittest.mock import Mock

from core.queries.level_up_screen_query import LevelUpScreenQuery
from core.queries.level_up_screen_query import LevelUpScreenQueryHandler


def test_level_up_screen_query_returns_players_with_unspent_skill_points():
    player_without_points = _player(
        player_id="player-1",
        full_name="No Points",
        level=1,
        technique=50,
        endurance=40,
        skill_points=0,
    )
    player_with_points = _player(
        player_id="player-2",
        full_name="Has Points",
        level=2,
        technique=55,
        endurance=45,
        skill_points=2,
    )
    provider = _club_provider({
        "club": _club([
            _slot(player_without_points),
            _slot(player_with_points),
        ]),
    })
    handler = LevelUpScreenQueryHandler(provider)

    result = handler(LevelUpScreenQuery(
        game_id="game",
        club_id="club",
    ))

    assert len(result.players) == 1
    assert result.players[0].player_id == "player-2"
    assert result.players[0].full_name == "Has Points"
    assert result.players[0].level == 2
    assert result.players[0].technique == 55
    assert result.players[0].endurance == 45
    assert result.players[0].available_skill_points == 2


def test_level_up_screen_query_returns_empty_list_for_missing_club():
    provider = _club_provider({})
    handler = LevelUpScreenQueryHandler(provider)

    result = handler(LevelUpScreenQuery(
        game_id="game",
        club_id="club",
    ))

    assert result.players == []


def _club_provider(clubs):
    provider = Mock()
    provider.get_clubs_for_game.return_value = clubs
    return provider


def _club(players):
    club = Mock()
    club.players = players
    return club


def _slot(player):
    slot = Mock()
    slot.player = player
    return slot


def _player(**attrs):
    player = Mock()
    for name, value in attrs.items():
        setattr(player, name, value)
    return player
