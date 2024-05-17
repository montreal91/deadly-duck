"""
Created Apr 09, 2019

@author montreal91
"""

import json
import os.path
import sys

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from configuration.application_context import ApplicationContext
from configuration.application_context import get_application_context
from core.attendance import DdAttendanceParams
from core.attendance import DdCourt
from core.financial import DdTransaction
from core.game import Game
from core.game import GameParams
from core.game import DdOpponentStruct
from core.match import DdExhaustionCalculator
from core.match import DdMatchParams
from core.match import DdLinearProbabilityCalculator
from core.player import DdPlayer
from core.player import DdPlayerReputationCalculator
from core.playoffs import DdPlayoffParams
from core.regular_championship import DdChampionshipParams

BOLD = "\033[;1m"
RESET = "\033[0;0m"


def UserAction(fun: Callable) -> Callable:
    """Helper decorator to handle user input."""

    def res(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except (AssertionError, ValueError) as error:
            print(error)
        except TypeError as error:
            print("Incorrect number of arguments.")
            print(error)

    return res


class SimplifiedApp:
    """Simple client for a game that runs in the console."""

    def __init__(
            self,
            starting_club: int,
            config_filename: str,
            game_id: str,
            load: bool = False
    ):
        self._manager_club_id = starting_club
        self._game_id = game_id
        self._game_service = get_application_context().game_service

        if not load:
            self._game_service.create_new_game(self._game_id, self._manager_club_id)

        self._actions = {}
        self._is_running = True

        self._InitActions()

    def run(self):
        """Runs the game."""

        print("Type ? for help.")
        while self._is_running and not self._game_is_over:
            self._PrintMain()
            self._ProcessInput()

    @property
    def _game_is_over(self) -> bool:
        return self._game_service.game_is_over(self._game_id)

    def _InitActions(self):
        self._actions["?"] = self.__action_help
        self._actions["agents"] = self.__action_agents
        self._actions["coach"] = self.__action_coach
        self._actions["c"] = self.__action_court
        self._actions["court"] = self.__action_court
        self._actions["fame"] = self.__action_fame
        self._actions["fire"] = self.__action_fire
        self._actions["hire"] = self.__action_hire
        self._actions["h"] = self.__action_history
        self._actions["history"] = self.__action_history
        self._actions["l"] = self.__action_list
        self._actions["list"] = self.__action_list
        self._actions["n"] = self.__action_next
        self._actions["next"] = self.__action_next
        self._actions["o"] = self.__action_opponent
        self._actions["opponent"] = self.__action_opponent
        self._actions["proceed"] = self.__action_proceed
        self._actions["q"] = self.__action_quit
        self._actions["quit"] = self.__action_quit
        self._actions["res"] = self.__action_results
        self._actions["s"] = self.__action_select
        self._actions["select"] = self.__action_select
        self._actions["sh"] = self.__action_show
        self._actions["show"] = self.__action_show
        self._actions["sign"] = self.__ActionSign
        self._actions["st"] = self.__ActionStandings
        self._actions["standings"] = self.__ActionStandings
        self._actions["t"] = self.__ActionTicket
        self._actions["ticket"] = self.__ActionTicket
        self._actions["u"] = self.__ActionUpcoming
        self._actions["upcoming"] = self.__ActionUpcoming

        self._actions["_$"] = self.__Action_Finances
        self._actions["_d"] = self.__Action_DropAccounts
        self._actions["_l"] = self.__Action_Levels
        self._actions["_m"] = self.__Action_Measure

    def _PrintMain(self):
        info: MainMenuInfo = self._game_service.get_main_screen_info(
            self._game_id,
            self._manager_club_id
        )

        print(f"\n{info.club_name}")
        print("Day:     {0:d}".format(info.day))
        print("Balance: ${0:d}".format(info.balance))
        print()

    def _ProcessInput(self):
        user_input = input(">> ").split("/")
        self._actions.setdefault(
            user_input[0], lambda *_: print("No such action.")
        )

        action = self._actions[user_input[0]]
        action(*user_input[1:])

    @UserAction
    def __Action_DropAccounts(self):
        for club in self._game._clubs.values():
            balance = club.account.balance
            balance = -balance + 100000
            club.account.ProcessTransaction(DdTransaction(balance, "Drop"))

    @UserAction
    def __action_fame(self):
        query_result = self._game_service.get_fames(self._game_id)

        for fame_row in query_result.fame_ratings:
            if fame_row.club_id == self._manager_club_id:
                print(BOLD, end="")
            print(f"{fame_row.club_name:20s}", fame_row.fame)
            if fame_row.club_id == self._manager_club_id:
                print(RESET, end="")

    @UserAction
    def __Action_Finances(self):
        for club in self._game._clubs.values():
            print(f"{club.name:20s}", club.account.balance)

    @UserAction
    def __Action_Levels(self):
        for pk, club in self._game._clubs.items():
            level_sum = sum(slot.player.level for slot in club.players)
            level_max = max(slot.player.level for slot in club.players)
            if pk == self._manager_club_id:
                sys.stdout.write(BOLD)
            print(f"{club.name:20s} {level_sum:3d} {level_max:2d}")
            if pk == self._manager_club_id:
                sys.stdout.write(RESET)

    @UserAction
    def __Action_Measure(self):
        import time
        dt1 = time.time()
        self._game.get_context(self._manager_club_id)
        dt2 = time.time()

        print(f"Time to calculate context: {dt2 - dt1:.4f}")

    @UserAction
    def __action_agents(self, sub_action: str, index: Optional[str] = None):
        assert sub_action in ("list", "hire")
        if sub_action == "hire":
            self._game_service.hire_free_agent(
                game_id=self._game_id,
                manager_club_id=self._manager_club_id,
                agent_id=int(index)
            )
            return

        agents = self._game_service.get_agents_list_screen_info(
            self._game_id,
            self._manager_club_id,
        )

        print(" #| Age|Technq|Endrnc| Spec| Contract | Name")
        print("__|____|______|______|_____|__________|_____________")
        for agent in agents:
            print(f"{agent.player_id:2d}|", end="")
            print(" {0:2d} |".format(agent.age), end="")
            print(
                f"{agent.technique:5.2f} |",
                end="",
            )
            print(
                "{0:5.2f} |".format(agent.endurance),
                end="",
            )
            print("{0:5s}|".format(agent.speciality), end="")
            print(f" ${agent.contract_cost:7d} |", end="")
            print(agent.name, end="")
            print()

    @UserAction
    def __action_coach(self, player_index: str, coach_index: str):
        self._game_service.select_coach_for_player(
            self._game_id,
            self._manager_club_id,
            int(coach_index),
            int(player_index),
        )

    @UserAction
    def __action_court(self, court: Optional[str] = None):
        if court is not None:
            self._game_service.select_court_for_club(
                self._game_id,
                self._manager_club_id,
                court
            )
            return

        court = self._game_service.get_court_info(
            self._game_id, self._manager_club_id
        )

        print("Capacity:    ", court.capacity)
        print("Rent cost:   ", court.rent_cost)
        print("Ticket price:", court.ticket_price)

    @UserAction
    def __action_fire(self, index: str):
        self._game_service.fire_player(
            self._game_id,
            self._manager_club_id,
            int(index)
        )

    @UserAction
    def __action_help(self):
        with open("core/help.txt") as help_file:
            print(help_file.read())

    @UserAction
    def __action_hire(self, surface: str):
        self._game_service.hire_player(
            self._game_id,
            self._manager_club_id,
            surface
        )

    @UserAction
    def __action_history(self, season: str):
        s = int(season)
        ctx = self._get_actual_context()
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
            users_club=self._manager_club_id,
        )
        if "Cup" in history[s - 1]:
            print("=" * 50)
            _PrintCupStandings(
                history[s - 1]["Cup"],
                ctx["clubs"],
                self._manager_club_id,
                3,
            )

    @UserAction
    def __action_list(self):
        print(" #| Age| Technique|Stm|Exh| Spec| Coach | Name")
        print("__|____|__________|___|___|_____|_______|_____________")

        info = self._game_service.get_player_list_info(
            self._game_id,
            self._manager_club_id,
        )

        for player in info.players:
            if player.is_selected:
                print(BOLD, end="")
            print("{0:2}|".format(player.player_id), end="")
            print(" {0:2d} |".format(player.age), end="")
            print(
                "{0:4.1f} /{1:4.1f}|".format(
                    round(player.actual_technique / 10, 1),
                    round(player.technique / 10, 1)
                ),
                end="",
            )
            print(
                "{0:3d}|".format(player.current_stamina),
                end="",
            )
            print(
                "{0:3d}|".format(player.exhaustion),
                end=""
            )
            print("{0:5s}|".format(player.speciality), end="")
            print(
                "   {0:1d}   |".format(
                    player.coach_level
                ),
                end=""
            )
            print(player.name, end="")
            if player.is_selected:
                print(RESET, end="")
            print()

        print("\nCurrent practice price:", "$" + str(info.practice_cost))

    @UserAction
    def __action_next(self):
        res = self._game_service.next_day(self._game_id)
        if not res.success:
            print("You have to select a player.")
            return

        self.__action_results()

    @UserAction
    def __action_opponent(self):
        context = self._get_actual_context()
        opponent: DdOpponentStruct = context["opponent"]
        if opponent is None:
            print("No opponents today.")
            return
        print(f"{BOLD}{opponent.club_name}{RESET}", end=" ")
        print("({})".format(
            "home" if opponent.player is not None else "away"
        ))
        if opponent.fame is not None:
            print("Fame:", opponent.fame)
        print("Match surface:", opponent.match_surface)
        print("_" * 30)

        if opponent.player is not None:
            _PrintPlayer(opponent.player, False)

    @UserAction
    def __action_proceed(self):
        self._game_service.proceed(self._game_id)

    @UserAction
    def __action_quit(self):
        self._is_running = False

    @UserAction
    def __action_results(self):
        context = self._get_actual_context()
        clubs = context["clubs"]
        pk = self._manager_club_id
        for res in context["last_results"]:
            exp = None
            if res.home_pk == pk:
                exp = DdPlayer.CalculateNewExperience(
                    res.home_sets,
                    res.away_player_snapshot["level"]
                )
            elif res.away_pk == pk:
                exp = DdPlayer.CalculateNewExperience(
                    res.away_sets,
                    res.home_player_snapshot["level"]
                )

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
                if res.home_pk == pk:
                    print("\nAttendance:", res.attendance)
                    print("Income:    ", res.income)
                sys.stdout.write(RESET)
            print()

    @UserAction
    def __action_select(self, index="0"):
        self._game_service.set_player(self._game_id, self._manager_club_id, int(index))

    @UserAction
    def __action_show(self, index: str):
        index = int(index)
        context = self._get_actual_context()
        players_data = context["user_players"]
        assert 0 <= index < len(players_data), "Incorrect player index"
        _PrintPlayer(
            players_data[index].player,
            own=True,
            contract_cost=players_data[index].contract_cost,
            next_contract=players_data[index].has_next_contract,
        )

    @UserAction
    def __ActionSign(self, player_index: str):
        self._game.SignPlayer(pk=self._manager_club_id, i=int(player_index))

    @UserAction
    def __ActionStandings(self):
        context = self._get_actual_context()
        if context["title"] == "Cup":
            _PrintCupStandings(
                context["standings"],
                context["clubs"],
                self._manager_club_id,
                3,
            )
        else:
            _PrintRegularStandings(
                context["standings"],
                context["clubs"],
                self._manager_club_id
            )

    @UserAction
    def __ActionTicket(self, ticket_price):
        self._game.SetTicketPrice(pk=self._manager_club_id, price=int(ticket_price))

    @UserAction
    def __ActionUpcoming(self):
        context = self._get_actual_context()
        for match in context["remaining_matches"][:5]:
            if match.home_pk == self._manager_club_id:
                print(context["clubs"][match.away_pk], "(home)")
            elif match.away_pk == self._manager_club_id:
                print(context["clubs"][match.home_pk], "(away)")
            else:
                raise Exception("Bad match {}".format(match))
        print(
            "\nRemaining matches:",
            len(context["remaining_matches"]),
        )

    def _get_actual_context(self):
        return self._game_service.get_game_context(self._game_id)


def _GetPlayerName(player_json: Dict[str, Any]) -> str:
    return (
        f"{player_json['first_name'][0]}. "
        f"{player_json['second_name'][0]}. "
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


def _PrintPlayer(
        player: DdPlayer,
        next_contract: bool,
        own: bool = False,
        contract_cost: Optional[int] = None
):
    string = (
        "Level {level:d}\n"
        "{bold}"
        "{full_name:s}\n\n"
        "{reset}"
        "Age:         {age:d}\n"
        "Technique:   {actual_technique:3.1f}/{technique:3.1f}\n"
        "Stamina:     {current_stamina:d}/{max_stamina:d}\n"
        "Exhaustion:  {exhaustion:d}\n\n"
        "Speciality:  {speciality:s}\n\n"
        "Sets won:    {sets_won:d}/{sets_played:d}\n"
        "Matches won: {matches_won:d}/{matches_played:d}\n"
    )
    print(string.format(
        full_name=player.full_name,
        level=player.level,
        actual_technique=round(player.actual_technique / 10, 1),
        technique=round(player.technique / 10, 1),
        endurance=player.endurance,
        exhaustion=player.exhaustion,
        age=player.age,
        speciality=player.speciality,
        current_stamina=player.current_stamina,
        max_stamina=player.max_stamina,
        sets_won=player.stats.sets_won,
        sets_played=player.stats.sets_played,
        matches_won=player.stats.matches_won,
        matches_played=player.stats.matches_played,
        bold=BOLD,
        reset=RESET,
    ))
    if own:
        print(f"Exp: {player.experience} / {player.next_level_exp}")
        print(f"Rep: {player.reputation}")
        if not next_contract:
            print(f"\nConract cost: ${contract_cost}")


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
    parser.add_argument(
        "--club",
        type=int,
        choices=range(16),
        default=0,
        help="Selects a specific club."
    )
    parser.add_argument(
        "--savename",
        type=str,
        default="default",
        help="The name of the file for save/load game."
    )

    parser.add_argument(
        "--load",
        help=(
            "Loads previously saved game from the specified filename if "
            "possible."
        ),
        action="store_true"
    )

    arguments = parser.parse_args()

    app = SimplifiedApp(
        starting_club=arguments.club,
        load=arguments.load,
        game_id=arguments.savename,
        config_filename="short"
    )
    app.run()
