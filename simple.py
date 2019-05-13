
"""
Created Apr 09, 2019

@author montreal91
"""

import os.path
import pickle
import sys

from typing import Dict
from typing import Callable

from simplified.game import DdGameDuck
from simplified.game import DdGameParams
from simplified.match import CalculateConstExhaustion
from simplified.match import LinearProbabilityFunction
from simplified.player import DdPlayer
from simplified.player import DdPlayerReputationCalculator
from simplified.player import ExhaustedLinearRecovery


BOLD = "\033[;1m"
RESET = "\033[0;0m"


class DdSimplifiedApp:
    """Simple client for a game that runs in the console."""

    _SAVE_FOLDER = ".saves"

    _actions: Dict[str, Callable]
    _game: DdGameDuck
    _is_running: bool
    _save_filename: str

    def __init__(
        self,
        starting_club: int,
        save_filename: str,
        load: bool = False
    ):
        self._save_path = os.path.join(self._SAVE_FOLDER, save_filename)

        if load:
            self._LoadGame()
        else:
            self._game = DdGameDuck(DdGameParams(
                exdiv_matches=2,
                exhaustion_function=CalculateConstExhaustion,
                exhaustion_per_set=2,
                indiv_matches=2,
                probability_function=LinearProbabilityFunction,
                recovery_day=4,
                recovery_function=ExhaustedLinearRecovery,
                playoff_clubs=8,
                reputation_function=DdPlayerReputationCalculator(6, 5),
                starting_club=starting_club,

            ))
        self._actions = {}
        self._is_running = True

        self._InitActions()

    def Run(self):
        """Runs game."""
        print("Type ? for help.")
        while self._is_running:
            self._PrintMain()
            self._ProcessInput()

    def _InitActions(self):
        self._actions["?"] = self.__ActionHelp
        self._actions["h"] = self.__ActionHistory
        self._actions["history"] = self.__ActionHistory
        self._actions["l"] = self.__ActionList
        self._actions["list"] = self.__ActionList
        self._actions["n"] = self.__ActionNext
        self._actions["next"] = self.__ActionNext
        self._actions["o"] = self.__ActionOpponent
        self._actions["opponent"] = self.__ActionOpponent
        self._actions["p"] = self.__ActionPractice
        self._actions["practice"] = self.__ActionPractice
        self._actions["q"] = self.__ActionQuit
        self._actions["quit"] = self.__ActionQuit
        self._actions["rem"] = self.__ActionRemaining
        self._actions["save"] = self.__ActionSave
        self._actions["res"] = self.__ActionResults
        self._actions["s"] = self.__ActionSelect
        self._actions["select"] = self.__ActionSelect
        self._actions["sh"] = self.__ActionShow
        self._actions["show"] = self.__ActionShow
        self._actions["st"] = self.__ActionStandings
        self._actions["standings"] = self.__ActionStandings

        self._actions["_m"] = self.__ActionMeasure

    def _LoadGame(self):
        if os.path.isfile(self._save_path):
            with open(self._save_path, "rb") as save_file:
                self._game = pickle.load(save_file)
                print("Game is loaded successfully.")
        else:
            print("This save does not exist yet.")

    def _PrintMain(self):
        ctx = self._game.context
        print("\nDay: {0:2d}".format(ctx["day"]))
        print()

    def _ProcessInput(self):
        user_input = input(">> ").split("/")
        self._actions.setdefault(
            user_input[0], lambda *_ : print("No such action.")
        )

        action = self._actions[user_input[0]]
        if len(user_input) - 1 in range(*_GetNumberOfArguments(action)):
            action(*user_input[1:])
        else:
            print("Your input is incorrect.")

    def __ActionHelp(self):
        with open("simplified/help.txt") as help_file:
            print(help_file.read())

    def __ActionHistory(self, season: str):
        try:
            s = int(season)
            ctx = self._game.context

            if s > len(ctx["history"]):
                print(f"Season {s} is not finished yet.")
                return
            if s < 1:
                print(f"Season should be a positive integer")
                return
            _PrintStandings(
                standings=ctx["history"][s - 1],
                club_names=ctx["clubs"],
                users_club=ctx["users_club"],
            )
        except ValueError:
            print("Season should be a valid integer.")

    def __ActionList(self):
        for i in range(len(self._game.context["user_players"])):
            print(i, end=" ")
            plr = self._game.context["user_players"][i]
            print("Age: {0:2d}".format(plr.json["age"]), end=" ")
            print(
                "Technique: {0:3.1f}/{1:3.1f}".format(
                    round(plr.json["actual_technique"] / 10, 1),
                    round(plr.json["technique"] / 10, 1)
                ),
                end=" ",
            )
            print(
                "Stamina: {0:3d}".format(plr.json["current_stamina"]),
                end=" ",
            )
            print(
                "Exhaustion: {0:3d}".format(plr.json["exhaustion"]),
                end=" "
            )
            print()

    def __ActionMeasure(self):
        import time
        t1 = time.time()
        context = self._game.context
        t2 = time.time()

        print(f"Time to calculate context: {t2 - t1:.4f}")

    def __ActionNext(self):
        recovery = self._game.context["is_recovery_day"]
        res = self._game.Update()
        if not res:
            print("You have to select a player.")
            return

        if not recovery:
            self.__ActionResults()

    def __ActionOpponent(self):
        opponent: DdPlayer = self._game.context["opponent"]
        if opponent is None:
            if self._game.context["is_recovery_day"]:
                print("No opponents today.")
            else:
                print("You are away.")
                print("The away team names its player first.")
            return

        print(opponent[0])
        _PrintPlayer(opponent[1], False)

    def __ActionPractice(self, p1="0", p2="1"):
        if p1 == p2:
            print("Player can't practice with oneself.")
            return
        try:
            self._game.SetPractice(int(p1), int(p2))
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionQuit(self):
        self._is_running = False

    def __ActionRemaining(self):
        print("Remaining matches:", self._game.context["remaining_matches"])

    def __ActionResults(self):
        clubs = self._game.context["clubs"]
        uk = self._game.context["users_club"]
        for res in self._game.context["last_results"]:
            exp = None
            if res.home_pk == uk:
                exp = res.home_exp
            elif res.away_pk == uk:
                exp = res.away_exp

            if exp is not None:
                sys.stdout.write(BOLD)
            print("{0:s} vs {1:s}\n{2:s}".format(
                    clubs[res.home_pk],
                    clubs[res.away_pk],
                    res.full_score,
                ))

            if exp is not None:
                print("Gained exp:", exp)
                sys.stdout.write(RESET)
            print()

    def __ActionSave(self):
        with open(self._save_path, "wb") as save_file:
            pickle.dump(self._game, save_file)
            print("The game is saved.")

    def __ActionSelect(self, index="0"):
        try:
            self._game.SelectPlayer(int(index))
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionShow(self, index="0"):
        try:
            index = int(index)
            player: DdPlayer = self._game.context["user_players"][index]
            _PrintPlayer(player, own=True)
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionStandings(self):
        context = self._game.context
        _PrintStandings(
            context["standings"],
            context["clubs"],
            context["users_club"]
        )


def _GetNumberOfArguments(function):
    max_ = function.__code__.co_argcount
    min_ = max_
    if function.__defaults__ is not None:
        min_ -= len(function.__defaults__)
    return min_ - 1, max_


def _PrintPlayer(player: DdPlayer, own=False):
    string = (
        "{initials:s} [{level:d}]\n"
        "Technique:  {actual_technique:3.1f} / {technique:3.1f}\n"
        "Endurance:  {endurance:3.1f}\n"
        "Exhaustion: {exhaustion:d}\n"
    )
    print(string.format(
        initials=player.initials,
        level=player.level,
        actual_technique=round(player.actual_technique / 10, 1),
        technique=round(player.technique / 10, 1),
        endurance=player.endurance,
        exhaustion=player.exhaustion,
    ))
    if own:
        print(f"Exp: {player.experience} / {player.next_level_exp}")
        print(f"Rep: {player.reputation}")


def _PrintStandings(standings, club_names, users_club):
    standings = sorted(
        standings,
        key=lambda x: (x.sets_won, x.games_won),
        reverse=True
    )
    for i in range(len(standings)):
        row = standings[i]
        if row.club_pk == users_club:
            sys.stdout.write(BOLD)
        print("{pos:02d} {sets:2d} {games:3d} {club_name:s}".format(
            club_name=club_names[row.club_pk],
            pos=i+1,
            sets=row.sets_won,
            games=row.games_won,
        ))
        if row.club_pk == users_club:
            sys.stdout.write(RESET)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--club", type=int, choices=range(16), default=0)
    parser.add_argument("--savename", type=str, default="default")
    parser.add_argument(
        "--load",
        help="Loads previously saved game if possible.",
        action="store_true"
    )

    args = parser.parse_args()

    app = DdSimplifiedApp(args.club, args.savename, args.load)
    app.Run()
