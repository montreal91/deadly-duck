
"""
Created Apr 09, 2019

@author montreal91
"""

from simplified.game import DdGameDuck
from simplified.game import DdGameParams


class DdSimplifiedApp:
    def __init__(self):
        self._game = DdGameDuck(DdGameParams(2, 44, 3))
        self._actions = {}
        self._is_running = True

        self._InitActions()

    def Run(self):
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
        self._actions["q"] = self.__ActionQuit
        self._actions["quit"] = self.__ActionQuit
        self._actions["rem"] = self.__ActionRemaining
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
                self._actions[user_input[0]](user_input[1])
        else:
            print("Your input is incorrect.")

    def __ActionList(self):
        for i in range(len(self._game.context["user_players"])):
            print(i, end=" ")
            plr = self._game.context["user_players"][i]
            print(
                "Technique: {0:3.1f}/{1:3.1f}".format(
                    plr.json["actual_technique"], plr.json["technique"]
                ),
                end=" ",
            )
            print(
                "Stamina: {0:3.1f}".format(plr.json["current_stamina"]),
                end=" ",
            )
            print(
                "Exhaustion: {0:3.1f}".format(plr.json["exhaustion"]),
                end=" "
            )
            print()

    def __ActionNext(self):
        res = self._game.Update()
        if not res:
            print("You have to select a player.")
            return
        print(self._game.context["last_score"])

    def __ActionQuit(self):
        self._is_running = False

    def __ActionRemaining(self):
        print("Remaining matches:", self._game.context["remaining_matches"])

    def __ActionSelect(self, index):
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

if __name__ == '__main__':
    app = DdSimplifiedApp()
    app.Run()
