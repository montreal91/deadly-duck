import time
from datetime import date

from core.game import Game
from core.game import GameParams
from core.competition import CompetitionType
from core.match import ExhaustionCalculator
from core.match import DdLinearProbabilityCalculator
from core.match_engine import MatchParams
from core.player import PlayerReputationCalculator
from core.playoffs import DdPlayoffParams
from core.ports.outbound.temporal_club_provider import TemporalClubProvider
from core.regular_championship import ChampionshipParams


def test_game_starts_on_first_season_calendar_date():
    game = _make_game()

    assert game.current_date == date(2082, 2, 21)
    assert game.get_context(_first_club_id(game))["day"] == "2082-Feb-21"


def test_successful_game_update_advances_calendar_date():
    game = _make_game()

    success, _ = game.update()

    assert success
    assert game.current_date == date(2082, 2, 22)
    assert game.get_context(_first_club_id(game))["day"] == "2082-Feb-22"


def test_next_season_starts_on_next_year_february_21():
    game = _make_game()
    game._history[-1][CompetitionType.CHAMPIONSHIP] = game.competition.standings

    game._next_season()
    game._advance_current_date()

    assert game.current_date == date(2083, 2, 21)
    assert game.get_context(_first_club_id(game))["day"] == "2083-Feb-21"


def _make_game():
    TemporalClubProvider.initialize()
    now = time.time_ns() // 1_000_000
    return Game(
        params=_game_params(),
        game_id="calendar-test",
        created_ts=now,
        updated_ts=now,
    )


def _first_club_id(game):
    return next(iter(game.clubs))


def _game_params():
    match_params = MatchParams(
        games_to_win=1,
        sets_to_win=1,
        exhaustion_function=ExhaustionCalculator(1),
        probability_function=DdLinearProbabilityCalculator(0.003),
        reputation_function=PlayerReputationCalculator(1, 1),
    )
    return GameParams(
        championship_params=ChampionshipParams(
            match_params=match_params,
            recovery_day=2,
            rounds=2,
            match_importance=1,
        ),
        playoff_params=DdPlayoffParams(
            series_matches_pattern=(True, True, False),
            length=8,
            gap_days=0,
            match_params=match_params,
            match_importance=1,
        ),
        contracts=[10000 for _ in range(30)],
        exhaustion_factor=8,
        is_hard=False,
        training_coefficient=1,
        years_to_simulate=0,
    )
