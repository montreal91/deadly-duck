"""
Created Aug 20, 2026

@author montreal91
"""
from types import SimpleNamespace

from core.queries.level_up_screen_query import LevelUpScreenQuery
from core.queries.level_up_screen_query import LevelUpScreenQueryHandler


def test_level_up_screen_query_returns_players_with_unspent_skill_points():
    player_without_points = _Player(
        player_id="player-1",
        full_name="No Points",
        level=1,
        technique=50,
        endurance=40,
        skill_points=0,
    )
    player_with_points = _Player(
        player_id="player-2",
        full_name="Has Points",
        level=2,
        technique=55,
        endurance=45,
        skill_points=2,
    )
    provider = _ClubProvider({
        "club": _Club([
            _Slot(player_without_points),
            _Slot(player_with_points),
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
    provider = _ClubProvider({})
    handler = LevelUpScreenQueryHandler(provider)

    result = handler(LevelUpScreenQuery(
        game_id="game",
        club_id="club",
    ))

    assert result.players == []


class _ClubProvider:
    def __init__(self, clubs):
        self._clubs = clubs

    def get_clubs_for_game(self, _game_id):
        return self._clubs


class _Club:
    def __init__(self, players):
        self.players = players


class _Slot:
    def __init__(self, player):
        self.player = player


class _Player(SimpleNamespace):
    pass
