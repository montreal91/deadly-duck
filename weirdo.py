
import json
import sys

from copy import deepcopy
from random import choice
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from app.data.game.player import DdPlayer
from app.data.game.player import PlayerModelComparator
from app.game.match_processor import DdMatchProcessor
from app.game.match_processor import LinearProbabilityFunction
from app.game.match_processor import NaiveProbabilityFunction
from configuration.config_game import DdGameplayConstants

from direct.showbase.ShowBase import ShowBase

from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point2
from panda3d.core import TextNode

import ipdb

def get_label(text: str, pos: Tuple[float, float]) -> OnscreenText:
    label = OnscreenText(text)
    label["fg"] = (1, 1, 1, 1)
    label["align"] = TextNode.ALeft
    label["scale"] = 0.05
    label["pos"] = pos
    return label


class DdGameDuck:
    def __init__(self):
        self._day = 0
        self._matches_to_play = 30
        self._recovery_day = 3
        self._exhaustion_per_set = 4
        self._selected_player = None
        self._last_score = ""

        with open("configuration/names.json", "r") as names_file:
            self._names = json.load(names_file)

        self._club1 = []
        self._club2 = []

        for i in range(5):
            age = DdGameplayConstants.STARTING_AGE.value + i

            self._club1.append(self._make_player(age, i * 200))
            self._club2.append(self._make_player(age, i * 200))

    @property
    def context(self) -> Dict[str, Any]:
        return dict(
            day=self._day,
            user_players=deepcopy(self._club1),
            cpu_players=deepcopy(self._club2),
            is_recovery_day=self._is_recovery_day(),
            score=self._score,
            matches_to_play=self._matches_to_play,
            last_score=self._last_score,
        )

    def select_player(self, i):
        assert i < len(self._club1)
        self._selected_player = i

    def update(self):
        # ipdb.set_trace(context=9)
        if self._is_recovery_day():
            self._recover(exhausted_recovery)
            self._day += 1
            return True

        if self._selected_player is None:
            return False

        self._play_one_day()
        self._selected_player = None
        self._day += 1
        return True

    def _is_player_required(self):
        return self._selected_player is None and self._day + 1 % self._recovery_day == 1

    def _is_recovery_day(self):
        return self._day % self._recovery_day == 0

    def _make_player(self, age: int, experience: int) -> DdPlayer:
        player = DdPlayer(
            technique_n=DdGameplayConstants.SKILL_BASE.value,
            endurance_n=DdGameplayConstants.SKILL_BASE.value,
            experience_n=0,
            exhaustion_n=0
        )
        player.pk_n = 0
        player.first_name_c = choice(self._names["names"])
        player.second_name_c = choice(self._names["names"])
        player.last_name_c = choice(self._names["surnames"])
        player.age_n = age

        player.AddExperience(experience)
        player.LevelUpAuto()

        player.current_stamina_n = player.max_stamina
        player.matches = 0
        player.sets = 0
        player.games = 0
        return player

    def _recover(self, recover_function):
        for player in self._club1:
            player.RecoverStamina(recover_function(player))

        for player in self._club2:
            player.RecoverStamina(recover_function(player))

    def _play_one_day(self):
        p1 = self._club1[self._selected_player]
        p2 = max(self._club2, key=PlayerModelComparator)

        mp = DdMatchProcessor(LinearProbabilityFunction)
        res = mp.ProcessMatch(p1, p2)

        home_experience = DdPlayer.CalculateNewExperience(res.home_sets, p2)
        away_experience = DdPlayer.CalculateNewExperience(res.away_sets, p1)


        p1.AddExperience(home_experience)
        p1.LevelUpAuto()
        p2.AddExperience(away_experience)
        p2.LevelUpAuto()

        p1.RemoveStaminaLostInMatch(res.home_stamina_lost)
        p2.RemoveStaminaLostInMatch(res.away_stamina_lost)

        exhaustion = (res.home_sets + res.away_sets) * self._exhaustion_per_set
        p1.exhaustion_n += exhaustion
        p2.exhaustion_n += exhaustion

        p1.matches += 1
        p1.sets += res.home_sets
        p1.games += res.home_games
        p2.matches += 1
        p2.sets += res.away_sets
        p2.games += res.away_games

        self._recover(exhausted_recovery)

        self._matches_to_play -= 1
        self._last_score = res.full_score

    @property
    def _score(self):
        # ipdb.set_trace(context=7)
        return dict(
            user=count_matches(self._club1),
            cpu=count_matches(self._club2),
        )


class DdPandaDuck(ShowBase):
    _PLAYER_STRING = (
        "{name:s} [{lvl:d}]\n"
        "Technique: {actual_tech:.1f} / {tech:.1f}\n"
        "Endurance: {endurance:.1f}\n"
        "Exhaustion: {exhaustion:3d}\n"
    )
    _PLAYER_VERTICAL_DELTA = 0.25
    def __init__(self):
        super().__init__()
        self._game = DdGameDuck()
        self._labels = {}
        self._user_player_labels = []
        self._cpu_player_labels = []

        self._init_labels()
        self._init_buttons()
        self._escape_text = get_label(
            "To quit the game\npress ESC",
            (-1.25, 0.9)
        )
        self.set_background_color((0, 0, 0))
        DirectButton(
            pos=(0, 0, -0.8),
            text="Next Turn",
            scale=0.06,
            pad=(0.2, 0.2),
            rolloverSound=None,
            clickSound=None,
            command=self._make_game_command(self._next_day)
        )
        self.accept("escape", sys.exit)

    def _init_buttons(self):
        y = 0.7
        for i in range(5):

            b = DirectButton(
                pos=(-1.15, 0, y - i * self._PLAYER_VERTICAL_DELTA - 0.05),
                text=f"Select {i+1}",
                scale=0.05,
                pad=(0.2, 0.2),
                rolloverSound=None,
                clickSound=None,
                command=self._make_game_command(self._print, i)
            )
            b.reparent_to(self._user_player_labels[i])

    def _init_labels(self):
        self._labels["day"] = get_label(
            text="",
            pos=(1.1, -0.9),
        )
        self._labels["remaining_matches"] = get_label(
            text="",
            pos=(0.5, -0.9),
        )
        self._labels["score"] = get_label(
            text="",
            pos=(0, 0.8),
        )
        self._labels["last_match"] = get_label(
            text="",
            pos=(0, 0.7),
        )

        y = 0.7
        for i in range(5):
            self._user_player_labels.append(get_label(
                text=self._PLAYER_STRING,
                pos=(-1.0, y - i * self._PLAYER_VERTICAL_DELTA)
            ))
            self._cpu_player_labels.append(get_label(
                text=self._PLAYER_STRING,
                pos=(0.65, y - i * self._PLAYER_VERTICAL_DELTA)
            ))
        self._update_labels()

    def _next_day(self):
        self._game.update()

    def _make_game_command(
            self, function: Callable, args: Optional[Any] = None
        ) -> Callable:
        if args is not None:
            def command():
                function(args)
                self._update_labels()
            return command
        def command():
            function()
            self._update_labels()
        return command

    def _update_labels(self):
        context = self._game.context
        # print(context["user_players"])
        # ipdb.set_trace(context=7)
        self._labels["day"].setText(f"Day {context['day']}")
        self._labels["remaining_matches"].setText(
            f"Remaining matches: {context['matches_to_play']}"
        )
        self._labels["score"].setText(
            f"{context['score']['user']} "
            f"{context['score']['cpu']}"
        )
        self._labels["last_match"].setText(context["last_score"])

        for i in range(len(context["user_players"])):
            player = context["user_players"][i]
            self._user_player_labels[i].setText(self._get_player_string(player))

        for i in range(len(context["cpu_players"])):
            player = context["cpu_players"][i]
            self._cpu_player_labels[i].setText(self._get_player_string(player))

    def _get_player_string(self, player: DdPlayer) -> str:
        return self._PLAYER_STRING.format(
            name=f"{player.first_name_c} {player.last_name_c}",
            lvl=player.level,
            actual_tech=player.actual_technique,
            tech=player.technique,
            endurance=player.endurance,
            exhaustion=player.exhaustion_n,
        )

    def _print(self, i):
        self._game.select_player(i)


def exhausted_recovery(player: DdPlayer) -> int:
    base = player.max_stamina
    res = base * (100 - player.exhaustion_n) / 100
    return int(round(res))

def count_matches(players: List[DdPlayer]) -> int:
    return sum(p.sets for p in players)

if __name__ == '__main__':
    pd = DdPandaDuck()
    pd.run()
