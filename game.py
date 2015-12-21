
from random import shuffle

from league import JLeague
from club   import JClub

class JStruct:
    pass


PROCESS_INPUT_CODES = JStruct()
PROCESS_INPUT_CODES.DEFAULT = 0
PROCESS_INPUT_CODES.HAS_TO_EXIT = 1
PROCESS_INPUT_CODES.HAVE_TO_SELECT_PLAYER = 2

club_names = [
    "Canberra Masters",
    "Sydney Cangaroos",
    "Dandenong Pianists",
    "Melbourne Slams",
    "Melbourne Rockets",
    "Darwin Genes",
]

tennis_players = 4

class JGame( object ):
    def __init__(self):
        super( JGame, self ).__init__()

        self._league        = JLeague(days=20)
        self._players_club  = self._SelectClub()
        t_players_list      = [i+1 for i in range(len(club_names) * tennis_players)]
        shuffle(t_players_list)
        for i in range(len(club_names)):
            if i + 1 == self._players_club:
                club = JClub(club_id=i+1, name=club_names[i], playable=True)
            else:
                club = JClub(club_id=i+1, name=club_names[i], playable=False)

            for j in range(tennis_players):
                club.AddPlayer(t_players_list.pop())
            self._league.AddClub(club)
        self._league.CreateSchedule()

    def _SelectClub(self):
        print("\nYou are starting your career as a manager for tennis semipro club in Australia.")
        print("Choose the club you want to manage.")
        print("Possible choices are:")
        i = 0
        for club in club_names:
            i += 1
            print(i, club)

        print("\nYour choice is: (enter corresponding number)")
        ui = 0
        while ui not in range(1, len(club_names) + 1):
            try:
                print("Please, enter number from 1 to {0:d}.".format(len(club_names)))
                ui = int(input(">>  "))
            except ValueError:
                ui = 0

        print("Your choice is ", club_names[int(ui) - 1])
        return ui

    def _ShowPlayerCurrentMatch(self):
        res = self._league.GetCurrentMatchByClubId(self._players_club)
        if res:
            print("Your match is")
            print("\t", str(res))
        else:
            print("You have no upcoming matches.")

    def _ShowCurrentStandings(self):
        res = self._league.GetCurrentStandings()
        for row in res:
            if row[0]:
                print(" +{0:20s} {1:2d}".format(row[1], row[2]))
            else:
                print("  {0:20s} {1:2d}".format(row[1], row[2]))
        return PROCESS_INPUT_CODES.DEFAULT

    def _ProcessShowCommand(self):
        print("Day:", self._league.current_day)
        if self._league.current_matches:
            print("Upcoming matches.")
            for match in self._league.current_matches:
                print(match)
        else:
            print("No matches for today.")
        return PROCESS_INPUT_CODES.DEFAULT

    def _ProcessNextCommand(self):
        if not self._IsPlayableClubReady():
            return PROCESS_INPUT_CODES.HAVE_TO_SELECT_PLAYER
        if self._league.current_matches:
            self._league.PlayCurrentMatches()
            print("Today's results")
            for match in self._league.current_matches:
                print("\t{0:s} {1:d}:{2:d}".format(str(match), match.score[0], match.score[1]))
            self._league.NextDay()
        else:
            print("All quiet today")
            self._league.NextDay()
        return PROCESS_INPUT_CODES.DEFAULT

    def _ProcessSelectCommand(self, tokens):
        club = self._league.GetClubById(self._players_club)
        if len(tokens) == 1 or "r" in tokens:
            club.SelectRandomPlayer()
            print("Randomly selected player is {0:2d}".format(club.selected_player))
            return PROCESS_INPUT_CODES.DEFAULT
        elif len(tokens) == 2:
            pl = int(tokens[1])
            if pl in club.players:
                club.SelectPlayerById(pl)
                print("You have selected player {0:2d} for the next match".format(pl))
                return PROCESS_INPUT_CODES.DEFAULT
            else:
                print("Your club does not have this player!")
                return PROCESS_INPUT_CODES.DEFAULT
        else:
            print("Please, enter a valid command.")
            return PROCESS_INPUT_CODES.DEFAULT

    def _ProcessMyPlayersCommand(self):
        club = self._league.GetClubById(self._players_club)
        for player in club.players:
            if club.selected_player == player:
                print("{0:2d} <".format(player))
            else:
                print("{0:2d}".format(player))
        return PROCESS_INPUT_CODES.DEFAULT

    def _ProcessUserInput(self, user_input):
        tokens = user_input.split()
        if "show" in tokens:
            return self._ProcessShowCommand()
        elif "q" in tokens:
            return PROCESS_INPUT_CODES.HAS_TO_EXIT
        elif "n" in tokens:
            return self._ProcessNextCommand()
        elif "m" in tokens:
            self._ShowPlayerCurrentMatch()
            return PROCESS_INPUT_CODES.DEFAULT
        elif "s" in tokens:
            return self._ProcessSelectCommand(tokens)
        elif "mp" in tokens:
            return self._ProcessMyPlayersCommand()
        elif "cs" in tokens:
            return self._ShowCurrentStandings()
        else:
            print("Please, enter a valid command")
            return PROCESS_INPUT_CODES.DEFAULT

    def _IsPlayableClubReady(self):
        selected = bool(self._league.GetClubById(self._players_club).selected_player)
        match = bool(self._league.GetCurrentMatchByClubId(self._players_club))
        if selected is False and match is True:
            return False
        else:
            return True

    def _ProcessEndOfSeason(self):
        print("\nThe season is over.\n")
        self._ShowCurrentStandings()

        print("\nDo you want to play another season? (Y/N)")
        ui = ""
        while not ui.upper() in ["Y", "N", "YES", "NO"]:
            print("Please, enter '[Y]es' or '[N]o'")
            ui = input()
        if ui.upper() == "Y" or ui.upper() == "YES":
            self._league.ProceedToNextSeason()
            print("\nWELCOME TO THE SEASON #{0:d}".format(self._league.current_season))
            return PROCESS_INPUT_CODES.DEFAULT
        else:
            return PROCESS_INPUT_CODES.HAS_TO_EXIT

    # Text-based interface for testing purposes
    def PlayTextGame(self):
        print("WELCOME TO THE SEASON #{0:d}".format(self._league.current_season))
        have_to_exit = False
        while not have_to_exit:
            res = self._ProcessUserInput(input("> "))
            if res == PROCESS_INPUT_CODES.HAS_TO_EXIT:
                have_to_exit = True
            elif res == PROCESS_INPUT_CODES.HAVE_TO_SELECT_PLAYER:
                print("You have to select player!")
                continue
            if self._league.current_day >= self._league.days:
                if self._ProcessEndOfSeason() == PROCESS_INPUT_CODES.HAS_TO_EXIT:
                    have_to_exit = True
                else:
                    have_to_exit = False


if __name__ == "__main__":
    game = JGame()
    game.PlayTextGame()
