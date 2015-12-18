
from league import JLeague


class JStruct:
    pass


PROCESS_INPUT_CODES             = JStruct()
PROCESS_INPUT_CODES.DEFAULT     = 0
PROCESS_INPUT_CODES.HAS_TO_EXIT = 1

class JGame( object ):
    def __init__(self):
        super( JGame, self ).__init__()

        self._league = JLeague()
        for i in range(5):
            self._league.AddTeam(i+1)
        self._league.CreateSchedule()
        self._players_club = 1

    def _ShowPlayerCurrentMatch(self):
        res = self._league.GetCurrentMatchByClubId(self._players_club)
        if res:
            print("Your match is")
            print("\t", str(res))
        else:
            print("You have no upcoming matches.")

    def _ProcessUserInput(self, user_input):
        if user_input == "show":
            print("Day:", self._league.current_day)
            print(self._league.current_matches)
            return PROCESS_INPUT_CODES.DEFAULT
        elif user_input == "q":
            return PROCESS_INPUT_CODES.HAS_TO_EXIT
        elif user_input == "n":
            self._league.PlayCurrentMatches()
            print("Today's results")
            for match in self._league.current_matches:
                print("\t{0:s} {1:d}:{2:d}".format(str(match), match.score[0], match.score[1]))
            self._league.NextDay()
            return PROCESS_INPUT_CODES.DEFAULT
        elif user_input == "m":
            self._ShowPlayerCurrentMatch()
            return PROCESS_INPUT_CODES.DEFAULT
        else:
            print("Please, enter a valid command")
            return PROCESS_INPUT_CODES.DEFAULT

    # Text-based interface for testing purposes
    def PlayTextGame(self):
        have_to_exit = False
        while not have_to_exit:
            if self._ProcessUserInput(input("> ")) == PROCESS_INPUT_CODES.HAS_TO_EXIT:
                have_to_exit = True
            if self._league.current_day >= self._league.days:
                print("The season is over")
                have_to_exit = True

if __name__ == "__main__":
    game = JGame()
    game.PlayTextGame()
