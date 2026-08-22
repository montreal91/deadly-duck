"""
Created Aug 22, 2026

@author montreal91
"""
from copy import deepcopy
from typing import Callable
from typing import Dict
from typing import NamedTuple

from core.match_result import MatchResult
from core.player import Player
from core.set_result import SetResult
from core.set_result import DdSetStatuses
from stat_tools import LoadedToss


class MatchParams(NamedTuple):
    """Passive class to store basic match parameters."""

    exhaustion_function: Callable[[int], int]
    probability_function: Callable[[float, float], float]
    reputation_function: Callable[[int], int]

    games_to_win: int = 6
    sets_to_win: int = 2


class MatchEngine:
    """This class encapsulates inner logic of a tennis match."""

    _GAP: int = 2

    _res: MatchResult
    _params: MatchParams
    _stamina_counter: Dict[str, int]

    def __init__(self, params: MatchParams):
        self._res = MatchResult()
        self._params = params
        self._stamina_counter = {
            "home": 0,
            "away": 0,
        }

    def process_match(
        self, home_player: Player, away_player: Player
    ) -> MatchResult:
        """Processes match and returns the results."""

        sets_played = 0
        self._res.home_player_snapshot = home_player.json
        self._res.away_player_snapshot = away_player.json

        while not self._is_match_over():
            set_result = self._process_set(
                home_player,
                away_player
            )
            sets_played += 1
            self._res.AddSetResult(set_result)

            home_player.AddReputation(
                self._reputation_function(set_result.home_games) * sets_played
            )
            away_player.AddReputation(
                self._reputation_function(set_result.away_games) * sets_played
            )

        home_player.add_experience(self._res.home_exp)
        away_player.add_experience(self._res.away_exp)

        home_player.RemoveStaminaLostInMatch(self._stamina_counter["home"])
        away_player.RemoveStaminaLostInMatch(self._stamina_counter["away"])

        exhaustion = self._exhaustion_function(sets_played)

        home_player.AddExhaustion(exhaustion)
        away_player.AddExhaustion(exhaustion)

        self._update_stats(player=home_player, is_home=True)
        self._update_stats(player=away_player, is_home=False)

        return deepcopy(self._res)

    def _is_set_over(self, home_games: int, away_games: int) -> bool:
        games_to_win = self._params.games_to_win
        cond1 = home_games >= games_to_win and home_games - away_games >= self._GAP
        cond2 = away_games >= games_to_win and away_games - home_games >= self._GAP

        return cond1 or cond2

    def _is_match_over(self) -> bool:
        home_won = self._res.home_sets == self._params.sets_to_win
        away_won = self._res.away_sets == self._params.sets_to_win
        return home_won or away_won

    def _process_set(self, home_player, away_player):
        home_games, away_games = 0, 0
        while not self._is_set_over(home_games, away_games):
            home_stamina = _calculate_actual_stamina(
                home_player,
                lost_stamina=self._stamina_counter["home"]
            )
            away_stamina = _calculate_actual_stamina(
                away_player,
                lost_stamina=self._stamina_counter["away"]
            )
            home_actual_skill = _calculate_actual_skill(
                home_player, home_stamina
            )
            away_actual_skill = _calculate_actual_skill(
                away_player, away_stamina
            )

            if home_actual_skill == 0:
                return SetResult(
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.HOME_RETIRED
                )
            elif away_actual_skill == 0:
                return SetResult(
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.AWAY_RETIRED
                )

            toss = LoadedToss(self._probability_function(
                home_actual_skill, away_actual_skill
            ))

            if toss:
                home_games += 1
            else:
                away_games += 1

            self._stamina_counter["home"] += _calculate_stamina_lost_in_game()
            self._stamina_counter["away"] += _calculate_stamina_lost_in_game()

        return SetResult(
            home_games=home_games,
            away_games=away_games,
            set_status=DdSetStatuses.REGULAR,
        )

    def _update_stats(self, player: Player, is_home: bool):
        sets_won = self._res.home_sets if is_home else self._res.away_sets

        home_won = int(self._res.home_sets > self._res.away_sets)
        away_won = int(self._res.home_sets < self._res.away_sets)
        matches_won = home_won if is_home else away_won

        player.stats.matches_played += 1
        player.stats.sets_played += (
            self._res.home_sets + self._res.away_sets
        )

        player.stats.matches_won += matches_won
        player.stats.sets_won += sets_won

    @property
    def _exhaustion_function(self) -> Callable[[int], int]:
        return self._params.exhaustion_function

    @property
    def _probability_function(self) -> Callable[[float, float], float]:
        return self._params.probability_function

    @property
    def _reputation_function(self) -> Callable[[int], int]:
        return self._params.reputation_function


def _calculate_actual_skill(player, actual_stamina=0):
    return player.calculate_actual_technique(actual_stamina)


def _calculate_actual_stamina(player, lost_stamina=0):
    return player.current_stamina - lost_stamina


def _calculate_stamina_lost_in_game():
    return 2