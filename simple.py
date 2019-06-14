
"""
Created Apr 09, 2019

@author montreal91
"""

import os.path
import pickle
import sys

from typing import Any
from typing import Dict
from typing import Callable

from simplified.game import DdGameDuck
from simplified.game import DdGameParams
from simplified.game import DdOpponentStruct
from simplified.match import DdExhaustionCalculator
from simplified.match import DdMatchParams
from simplified.match import LinearProbabilityFunction
from simplified.player import DdPlayer
from simplified.player import DdPlayerReputationCalculator
from simplified.player import ExhaustedLinearRecovery
from simplified.playoffs import DdPlayoffParams
from simplified.regular_championship import DdChampionshipParams


BOLD = "\033[;1m"
RESET = "\033[0;0m"


class DdSimplifiedApp:
    """Simple client for a game that runs in the console."""

    _SAVE_FOLDER = ".saves"

    _club_pk: int
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
        self._club_pk = starting_club

        if load:
            self._LoadGame()
        else:
            match_params = DdMatchParams(
                speciality_bonus=11,
                games_to_win=6,
                sets_to_win=2,
                exhaustion_function=DdExhaustionCalculator(3),
                reputation_function=DdPlayerReputationCalculator(6, 5),
                probability_function=LinearProbabilityFunction,
            )
            championship_params = DdChampionshipParams(
                match_params=match_params,
                recovery_day=4,
                rounds=2,
            )
            playoff_params = DdPlayoffParams(
                series_matches_pattern=(
                    True, True, False, False, True, False, True,
                ),
                length=8,
                gap_days=1,
                match_params=match_params,
            )
            self._game = DdGameDuck(DdGameParams(
                championship_params=championship_params,
                playoff_params=playoff_params,
                recovery_function=ExhaustedLinearRecovery,
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
        self._actions["coach"] = self.__ActionCoach
        self._actions["fire"] = self.__ActionFire
        self._actions["hire"] = self.__ActionHire
        self._actions["h"] = self.__ActionHistory
        self._actions["history"] = self.__ActionHistory
        self._actions["l"] = self.__ActionList
        self._actions["list"] = self.__ActionList
        self._actions["n"] = self.__ActionNext
        self._actions["next"] = self.__ActionNext
        self._actions["o"] = self.__ActionOpponent
        self._actions["opponent"] = self.__ActionOpponent
        self._actions["proceed"] = self.__ActionProceed
        self._actions["q"] = self.__ActionQuit
        self._actions["quit"] = self.__ActionQuit
        self._actions["save"] = self.__ActionSave
        self._actions["res"] = self.__ActionResults
        self._actions["s"] = self.__ActionSelect
        self._actions["select"] = self.__ActionSelect
        self._actions["sh"] = self.__ActionShow
        self._actions["show"] = self.__ActionShow
        self._actions["st"] = self.__ActionStandings
        self._actions["standings"] = self.__ActionStandings
        self._actions["u"] = self.__ActionUpcoming
        self._actions["upcoming"] = self.__ActionUpcoming

        self._actions["_f"] = self.__ActionFame
        self._actions["_m"] = self.__ActionMeasure


    def _LoadGame(self):
        if os.path.isfile(self._save_path):
            with open(self._save_path, "rb") as save_file:
                self._game = pickle.load(save_file)
                self._club_pk = self._game.context["users_club"]
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
            user_input[0], lambda *_: print("No such action.")
        )

        action = self._actions[user_input[0]]
        if len(user_input) - 1 in range(*_GetNumberOfArguments(action)):
            action(*user_input[1:])
        else:
            print("Your input is incorrect.")

    def __ActionCoach(self, player_index: str, coach_index: str):
        try:
            pi = int(player_index)
            ci = int(coach_index)
            self._game.SelectCoachForPlayer(
                coach_index=ci, player_index=pi, pk=self._club_pk
            )
        except (AssertionError, ValueError) as error:
            print(error)

    def __ActionFame(self):
        for club in self._game._clubs.values():
            print(f"{club.name:20s}", club.fame)

    def __ActionFire(self, index: str):
        try:
            i = int(index)
            self._game.FirePlayer(i, self._club_pk)
        except (AssertionError, ValueError) as error:
            print(error)

    def __ActionHelp(self):
        with open("simplified/help.txt") as help_file:
            print(help_file.read())

    def __ActionHire(self, surface: str):
        try:
            self._game.HirePlayer(surface, self._club_pk)
        except AssertionError as error:
            print(error)

    def __ActionHistory(self, season: str):
        try:
            s = int(season)
            ctx = self._game.context
            history = ctx["history"]

            if s > len(history) or history[s - 1] == {}:
                print(f"Season {s} is not finished yet.")
                return
            if s < 1:
                print(f"Season should be a positive integer")
                return
            _PrintRegularStandings(
                standings=history[s - 1]["Championship"],
                club_names=ctx["clubs"],
                users_club=ctx["users_club"],
            )
            if "Cup" in history[s - 1]:
                print("=" * 50)
                _PrintCupStandings(
                    history[s-1]["Cup"],
                    ctx["clubs"],
                    ctx["users_club"],
                    3,
                )
        except ValueError:
            print("Season should be a valid integer.")

    def __ActionList(self):
        print(" #| Age| Technique|Stm|Exh| Spec| Coach | Name")
        print("__|____|__________|___|___|_____|_______|_____________")
        ctx = self._game.context
        for i in range(len(ctx["user_players"])):
            print("{0:2}|".format(i), end="")
            plr: DdPlayer = ctx["user_players"][i].player
            print(" {0:2d} |".format(plr.json["age"]), end="")
            print(
                "{0:4.1f} /{1:4.1f}|".format(
                    round(plr.json["actual_technique"] / 10, 1),
                    round(plr.json["technique"] / 10, 1)
                ),
                end="",
            )
            print(
                "{0:3d}|".format(plr.json["current_stamina"]),
                end="",
            )
            print(
                "{0:3d}|".format(plr.json["exhaustion"]),
                end=""
            )
            print("{0:5s}|".format(plr.json["speciality"]), end="")
            print(
                "   {0:1d}   |".format(
                    ctx["user_players"][i].coach_level
                ),
                end=""
            )
            print(plr.json["first_name"], plr.json["last_name"], end="")
            print()

    def __ActionMeasure(self):
        import time
        t1 = time.time()
        context = self._game.context
        t2 = time.time()

        print(f"Time to calculate context: {t2 - t1:.4f}")

    def __ActionNext(self):
        res = self._game.Update()
        if not res:
            print("You have to select a player.")
            return

        self.__ActionResults()

    def __ActionOpponent(self):
        opponent: DdOpponentStruct = self._game.context["opponent"]
        if opponent is None:
            print("No opponents today.")
            return
        print(opponent.club_name, end=" ")
        print("({})".format(
            "home" if opponent.player is not None else "away"
        ))
        print("Match surface:", opponent.match_surface)
        print("_" * 30)

        if opponent.player is not None:
            _PrintPlayer(opponent.player, False)

    def __ActionProceed(self):
        self._game.ProceedToNextCompetition()

    def __ActionQuit(self):
        self._is_running = False

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
            print(
                f"{clubs[res.home_pk]} vs "
                f"{clubs[res.away_pk]}\n"
                f"[{res.home_player_snapshot['level']}] "
                f"{_GetPlayerName(res.home_player_snapshot)} vs "
                f"[{res.away_player_snapshot['level']}] "
                f"{_GetPlayerName(res.away_player_snapshot)}\n"
                f"{res.full_score}"
            )

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
            self._game.SelectPlayer(int(index), self._club_pk)
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionShow(self, index="0"):
        try:
            index = int(index)
            player: DdPlayer = self._game.context["user_players"][index].player
            _PrintPlayer(player, own=True)
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionStandings(self):
        context = self._game.context
        if context["title"] == "Cup":
            _PrintCupStandings(
                context["standings"],
                context["clubs"],
                context["users_club"],
                3,
            )
        else:
            _PrintRegularStandings(
                context["standings"],
                context["clubs"],
                context["users_club"]
            )

    def __ActionUpcoming(self):
        context = self._game.context
        for match in context["remaining_matches"][:5]:
            if match.home_pk == self._club_pk:
                print(context["clubs"][match.away_pk], "(home)")
            elif match.away_pk == self._club_pk:
                print(context["clubs"][match.home_pk], "(away)")
            else:
                raise Exception("Bad match {}".format(match))
        print(
            "\nRemaining matches:",
            len(context["remaining_matches"]),
        )



def _GetNumberOfArguments(function):
    max_ = function.__code__.co_argcount
    min_ = max_
    if function.__defaults__ is not None:
        min_ -= len(function.__defaults__)
    return min_ - 1, max_


def _GetPlayerName(player_json: Dict[str, Any]) -> str:
    return (
        f"{player_json['first_name']} "
        f"{player_json['second_name']} "
        f"{player_json['last_name']}"
    )


def _PrintCupStandings(series, club_names, users_club, rounds):
    def RoundIndexGenerator(n):
        first = 0
        for i in range(n):
            res = list(range(first, first + 2 ** (n - i - 1)))
            first += len(res)
            yield i, res
    row_string = (
        "{top_name:s} vs {bottom_name:s}\n"
        "    {top_score:d}:{bottom_score:n}"
    )
    for i, _round in RoundIndexGenerator(rounds):
        if _round[0] == len(series):
            break
        print(f"Round {i + 1}")
        for j in _round:
            row = series[j]
            if users_club in row["clubs"]:
                sys.stdout.write(BOLD)
            print(row_string.format(
                top_name=club_names[row["clubs"][0]],
                bottom_name=club_names[row["clubs"][1]],
                top_score=row["score"][0],
                bottom_score=row["score"][1],
            ))
            if users_club in row["clubs"]:
                sys.stdout.write(RESET)
        print()


def _PrintPlayer(player: DdPlayer, own=False):
    string = (
        "{initials:s} [{level:d}]\n"
        "Technique:  {actual_technique:3.1f} / {technique:3.1f}\n"
        "Endurance:  {endurance:3.1f}\n"
        "Stamina:    {current_stamina:d} / {max_stamina:d}\n"
        "Exhaustion: {exhaustion:d}\n\n"
        "Speciality: {speciality:s}\n"
    )
    print(string.format(
        initials=player.initials,
        level=player.level,
        actual_technique=round(player.actual_technique / 10, 1),
        technique=round(player.technique / 10, 1),
        endurance=player.endurance,
        exhaustion=player.exhaustion,
        speciality=player.speciality,
        current_stamina=player.current_stamina,
        max_stamina=player.max_stamina,
    ))
    if own:
        print(f"Exp: {player.experience} / {player.next_level_exp}")
        print(f"Rep: {player.reputation}")


def _PrintRegularStandings(standings, club_names, users_club):
    standings = sorted(
        standings,
        key=lambda x: (x.sets_won, x.games_won),
        reverse=True
    )
    for i, row in enumerate(standings, 1):
        if row.club_pk == users_club:
            sys.stdout.write(BOLD)
        print("{pos:02d} {sets:2d} {games:3d} {club_name:s}".format(
            club_name=club_names[row.club_pk],
            pos=i,
            sets=row.sets_won,
            games=row.games_won,
        ))
        if row.club_pk == users_club:
            sys.stdout.write(RESET)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Short description.")
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
