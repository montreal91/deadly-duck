
from league import JLeague

class JGame( object ):
    def __init__(self):
        super( JGame, self ).__init__()

        self._league = JLeague()
        for i in range(5):
            self._league.AddTeam(i+1)
        self._league.CreateSchedule()
        self._players_club = 1

    # Text-based interface for testing purposes
    def PlayTextGame(self):
        have_to_exit = False
        while not have_to_exit:
            user_input = input("> ")
            if user_input == "show":
                print("Day:", self._league.current_day)
                print(self._league.current_matches)
            elif user_input == "q":
                have_to_exit = True
            elif user_input == "n":
                print("Today's results")
                for match in self._league.current_matches:
                    res = self._league.QuickSimResult()
                    print("\t#{0:d} {1:d}:{2:d} #{3:d}".format(match[0], res[0], res[1], match[1]))
                self._league.NextDay()
            elif user_input == "m":
                res = self._league.GetCurrentMatchByClubId(self._players_club)
                if res:
                    print("Your match is")
                    print("\t", res)
                else:
                    print("You have no upcoming matches.")
            else:
                print("Please, enter a valid command")
            if self._league.current_day >= self._league.days:
                print("The season is over")
                have_to_exit = True

if __name__ == "__main__":
    game = JGame()
    game.PlayTextGame()
