"""
Match processing orchestration.

Created Aug 22, 2026

@author montreal91
"""
from typing import Dict
from typing import List

from core.club import Club
from core.match_engine import MatchEngine
from core.match_engine import MatchParams
from core.match_result import MatchResult
from core.scheduled_match import ScheduledMatch


def process_matches(
        matches: List[ScheduledMatch],
        clubs: Dict[str, Club],
        match_params: MatchParams,
) -> List[MatchResult]:
    """Processes scheduled matches without mutating competition state."""
    results = []

    for match in matches:
        processor = MatchEngine(match_params)

        home_selected_player = clubs[match.home_pk].selected_player
        if home_selected_player is None:
            raise Exception("Bad home player")
        away_selected_player = clubs[match.away_pk].selected_player
        if away_selected_player is None:
            raise Exception("Bad away player")

        result = processor.process_match(
            home_selected_player,
            away_selected_player,
        )

        result.match_id = match.match_id
        result.home_pk = match.home_pk
        result.away_pk = match.away_pk
        results.append(result)

    return results
