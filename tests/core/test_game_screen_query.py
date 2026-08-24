"""
Created Aug 24, 2026

@author montreal91
"""
from types import SimpleNamespace
from typing import Dict

from core.club import Club
from core.competition import CompetitionType
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.queries.game_screen_query import GameScreenGuiQueryHandler
from core.scheduled_match import ScheduledMatch


def test_game_screen_query_converts_remaining_matches_to_upcoming_days():
    first_match = ScheduledMatch("manager", "opponent")
    second_match = ScheduledMatch("opponent", "manager")
    game = _Game(
        current_matches=[first_match],
        remaining_matches=[first_match, None, second_match],
    )
    handler = GameScreenGuiQueryHandler(
        game_repository=_GameRepository(game),
        club_provider=_ClubProvider({
            "manager": _Club("Manager Club"),
            "opponent": _Club("Opponent Club"),
        }),
    )

    result = handler("game", "manager")

    assert result.upcoming_days[0].day == "2082-Feb-21"
    assert result.upcoming_days[0].match.opponent_club_name == "Opponent Club"
    assert result.upcoming_days[0].match.home_away == "Home"
    assert result.upcoming_days[1].day == "2082-Feb-22"
    assert result.upcoming_days[1].match is None
    assert result.upcoming_days[2].day == "2082-Feb-23"
    assert result.upcoming_days[2].match.opponent_club_name == "Opponent Club"
    assert result.upcoming_days[2].match.home_away == "Away"


class _GameRepository:
    def __init__(self, game):
        self._game = game

    def get_game(self, _game_id):
        return self._game


class _ClubProvider(TemporalClubProvider):
    def __init__(self, clubs):
        super().__init__()
        self._clubs = clubs

    def get_clubs_for_game(self, game_id: str) -> Dict[str, Club]:
        return self._clubs


class _Game:
    def __init__(self, current_matches, remaining_matches):
        self.competition = SimpleNamespace(current_matches=current_matches)
        self._remaining_matches = remaining_matches

    def get_context(self, _manager_club_id):
        return {
            "day": "2082-Feb-21",
            "history": [{}],
            "balance": 0,
            "club_name": "Manager Club",
            "competition": "Regular Season",
            "competition_type": CompetitionType.CHAMPIONSHIP,
            "has_matches": True,
            "remaining_matches": self._remaining_matches,
            "standings": [],
        }


class _Club:
    def __init__(self, name):
        self.name = name
        self.players = []
