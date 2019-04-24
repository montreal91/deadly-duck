
"""
Created Apr 09, 2019

@author montreal91
"""

from simplified.game import DdGameDuck
from simplified.game import DdGameParams
from simplified.player import DdPlayer


class DdSimplifiedApp:
    """Simple client for a game that runs in the console."""

    def __init__(self):
        self._game = DdGameDuck(DdGameParams(2, 44, 3))
        self._actions = {}
        self._is_running = True

        self._InitActions()

    def Run(self):
        """Runs game."""

        while self._is_running and not self._game.season_over:
            self._PrintMain()
            self._ProcessInput()

        if self._is_running:
            print("_" * 80)
            print("Final standings\n")
            self._actions["standings"]()

    def _InitActions(self):
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
        self._actions["res"] = self.__ActionResults
        self._actions["s"] = self.__ActionSelect
        self._actions["select"] = self.__ActionSelect
        self._actions["st"] = self.__ActionStandings
        self._actions["standings"] = self.__ActionStandings

    def _PrintMain(self):
        ctx = self._game.context
        print("\nDay: {0:2d}".format(ctx["day"]))
        print()

    def _ProcessInput(self):
        user_input = input(">> ").split("/")

        if user_input[0] in self._actions:
            if len(user_input) == 1:
                self._actions[user_input[0]]()
            else:
                self._actions[user_input[0]](*user_input[1:])
        else:
            print("Your input is incorrect.")

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

        _PrintPlayer(opponent, False)

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
        res = self._game.context["last_results"]
        print("{0:s} vs {1:s}\n{2:s}".format(
                clubs[res.home_pk],
                clubs[res.away_pk],
                res.full_score,
            ))
        print("Your player has gained", end=" ")
        if self._game.context["users_club"] == res.home_pk:
            print(res.home_exp, end=" ")
        else:
            print(res.away_exp, end=" ")
        print("exp.")

    def __ActionSelect(self, index="0"):
        try:
            self._game.SelectPlayer(int(index))
        except AssertionError:
            print("Your input is incorrect (wrong index).")
        except ValueError:
            print("Please, input a correct integer.")

    def __ActionStandings(self):
        standings = sorted(
            self._game.context["standings"],
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True
        )
        for i in range(len(standings)):
            row = standings[i]
            print("{pos:02d} {sets:2d} {games:3d} {club_name:s}".format(
                club_name=row.club_name,
                pos=i+1,
                sets=row.sets_won,
                games=row.games_won,
            ))


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


if __name__ == '__main__':
    app = DdSimplifiedApp()
    app.Run()
