"""
Created Aug 22, 2026

@author montreal91
"""
from core.match_engine import MatchParams
from core.match import ExhaustionCalculator
from core.match import DdLinearProbabilityCalculator
from core.match_result import MatchResult
from core.player import PlayerReputationCalculator
from core.playoffs import DdPlayoffParams
from core.playoffs import Playoff
from core.playoffs import PlayoffSeed
from core.playoffs import DdPlayoffSeries
from core.regular_championship import ChampionshipParams
from core.regular_championship import RegularChampionship
from core.scheduled_match import ScheduledMatch
from core.set_result import DdSetStatuses
from core.set_result import SetResult


def test_scheduled_match_has_stable_id():
    match = ScheduledMatch("home", "away")

    assert match.match_id is not None
    assert match.match_id != ScheduledMatch("home", "away").match_id


def test_regular_championship_applies_current_results_by_match_id():
    competition = RegularChampionship(
        club_ids=["home", "away"],
        params=_championship_params(),
    )
    competition._schedule = [[ScheduledMatch("home", "away")]]
    match = competition.current_matches[0]
    result = _match_result(match)

    competition.apply_results([result])

    assert competition.day == 1
    assert competition.competition_id is not None
    assert match.is_played
    assert [r.match_id for r in competition.results_for_tests] == [result.match_id]
    assert competition.standings[0].matches_played == 1
    assert competition.standings[1].matches_played == 1


def test_regular_championship_rejects_results_for_wrong_match_id():
    competition = RegularChampionship(
        club_ids=["home", "away"],
        params=_championship_params(),
    )
    competition._schedule = [[ScheduledMatch("home", "away")]]
    result = _match_result(ScheduledMatch("home", "away"))

    try:
        competition.apply_results([result])
    except AssertionError as exc:
        assert str(exc) == "Results do not match current scheduled matches."
    else:
        raise AssertionError("Expected result validation to fail.")


def test_club_schedule_days_preserve_empty_days_between_matches():
    competition = RegularChampionship(
        club_ids=["home", "away", "other-1", "other-2"],
        params=_championship_params(),
    )
    first_match = ScheduledMatch("home", "away")
    second_match = ScheduledMatch("away", "home")
    competition._schedule = [
        [first_match],
        None,
        [second_match],
        None,
    ]

    schedule = competition.get_club_schedule_days("home")

    assert schedule == [first_match, None, second_match]


def test_playoff_has_ids_for_competition_series_and_matches():
    playoff = Playoff(
        params=_playoff_params(),
        seeds=_playoff_seeds(8),
    )
    match = _first_playoff_match(playoff)

    assert playoff.competition_id is not None
    assert match.match_id is not None
    assert match.playoff_series_id is not None
    assert not hasattr(match, "series")


def test_playoff_standings_include_seeds():
    seeds = _playoff_seeds(8)
    playoff = Playoff(
        params=_playoff_params(),
        seeds=seeds,
    )
    seed_by_club_id = {
        seed.club_id: seed.seed
        for seed in seeds
    }

    for standing in playoff.standings:
        for club_id, seed in zip(standing["clubs"], standing["seeds"]):
            assert seed == seed_by_club_id[club_id]


def test_playoff_applies_results_to_series_by_series_id():
    playoff = Playoff(
        params=_playoff_params(),
        seeds=_playoff_seeds(8),
    )
    first_match = _first_playoff_match(playoff)
    results = [
        _match_result(match)
        for match in playoff.current_matches
    ]

    playoff.apply_results(results)

    series = playoff._series_by_id[first_match.playoff_series_id]
    assert first_match.is_played
    assert series.score == (1, 0)


def test_playoff_series_accepts_one_missing_club_as_bye():
    series = DdPlayoffSeries(_playoff_params())

    series.pair = ("club", None)

    assert series.winner == "club"
    assert series.score == ("", "")


def test_playoff_series_rejects_two_missing_clubs():
    series = DdPlayoffSeries(_playoff_params())

    try:
        series.pair = (None, None)
    except AssertionError as exc:
        assert str(exc) == "Playoff series should have at least one club."
    else:
        raise AssertionError("Expected playoff series validation to fail.")


def test_twelve_club_playoff_draws_full_preliminary_round():
    playoff = Playoff(
        params=_playoff_params(length=12),
        seeds=_playoff_seeds(12),
    )
    preliminary_seed_pairs = [
        standing["seeds"]
        for standing in playoff.standings
    ]
    scheduled_seed_pairs = [
        {
            _seed_for_club(match.home_pk),
            _seed_for_club(match.away_pk),
        }
        for match in playoff.current_matches
    ]

    assert len(preliminary_seed_pairs) == 8
    assert len([
        pair
        for pair in preliminary_seed_pairs
        if "" in pair
    ]) == 4
    assert len(scheduled_seed_pairs) == 4
    assert all(not pair.intersection({1, 2, 3, 4}) for pair in scheduled_seed_pairs)
    assert all(pair.intersection({5, 6, 7, 8}) for pair in scheduled_seed_pairs)
    assert all(pair.intersection({9, 10, 11, 12}) for pair in scheduled_seed_pairs)


def test_twelve_club_playoff_adds_protected_seeds_after_preliminary_round():
    playoff = Playoff(
        params=_playoff_params(
            length=12,
            series_matches_pattern=(True,),
        ),
        seeds=_playoff_seeds(12),
    )
    preliminary_match_winners = {
        match.home_pk
        for match in playoff.current_matches
    }

    playoff.apply_results([
        _match_result(match)
        for match in playoff.current_matches
    ])

    quarterfinal_seed_pairs = [
        {
            _seed_for_club(match.home_pk),
            _seed_for_club(match.away_pk),
        }
        for match in playoff.current_matches
    ]

    assert len(quarterfinal_seed_pairs) == 4
    assert {1, 2, 3, 4} == {
        seed
        for pair in quarterfinal_seed_pairs
        for seed in pair.intersection({1, 2, 3, 4})
    }
    assert preliminary_match_winners == {
        club_id
        for match in playoff.current_matches
        for club_id in (match.home_pk, match.away_pk)
        if _seed_for_club(club_id) > 4
    }


def _first_playoff_match(playoff):
    while playoff.current_matches is None:
        playoff.apply_results([])
    return playoff.current_matches[0]


def _playoff_seeds(length):
    return [
        PlayoffSeed(club_id=str(i), seed=i + 1)
        for i in range(length)
    ]


def _seed_for_club(club_id):
    return int(club_id) + 1


def _match_result(match):
    result = MatchResult()
    result.match_id = match.match_id
    result.home_pk = match.home_pk
    result.away_pk = match.away_pk
    result.AddSetResult(SetResult(
        home_games=6,
        away_games=4,
        set_status=DdSetStatuses.REGULAR,
    ))
    result.AddSetResult(SetResult(
        home_games=6,
        away_games=4,
        set_status=DdSetStatuses.REGULAR,
    ))
    return result


def _championship_params():
    return ChampionshipParams(
        match_params=_match_params(),
        recovery_day=2,
        rounds=2,
        match_importance=1,
    )


def _playoff_params(length=8, series_matches_pattern=(True, True, False)):
    return DdPlayoffParams(
        series_matches_pattern=series_matches_pattern,
        length=length,
        gap_days=0,
        match_params=_match_params(),
        match_importance=1,
    )


def _match_params():
    return MatchParams(
        exhaustion_function=ExhaustionCalculator(1),
        probability_function=DdLinearProbabilityCalculator(0.003),
        reputation_function=PlayerReputationCalculator(6, 5),
    )
