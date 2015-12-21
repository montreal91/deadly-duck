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
    "Sydney Kangaroos",
    "Dandenong Pianists",
    "Melbourne Slams",
    "Melbourne Rockets",
    "Darwin Genes",
    "Kingston Whales",
    "Brisbane Rangers",
    "Adelaide Thrashers",
    "Perth Penguins"
]

tennis_players = 4

class JGame( object ):
    def __init__(self):
        super( JGame, self ).__init__()
        params              = self._SetupGameSettings()
        self._league        = JLeague(
            days=params["days"],
            divisions=params["divs"],
            indiv_matches=params["in_div_games"],
            exdiv_matches=params["ex_div_games"]
        )
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

    def _SetupGameSettings(self):
        res = {}
        ui = 0
        while ui not in range(1, 5):
            try:
                print("Input number of divisions (preferably 1-4):")
                ui = int(input(">>  "))
            except ValueError:
                ui = 0
        res["divs"] = ui
        ui = 0
        while ui not in (2, 4, 6):
            try:
                print("Input even number of games inside divisions (preferably 2, 4, 6):")
                ui = int(input(">>  "))
            except ValueError:
                ui = 0
        res["in_div_games"] = ui
        if res["divs"] > 1:
            ui = 0
            while ui not in (2, 4, 6):
                try:
                    print("Input even number of games outside divisions (preferably 2, 4, 6):")
                    ui = int(input(">>  "))
                except ValueError:
                    ui = 0
            res["ex_div_games"] = ui
        else:
            res["ex_div_games"] = 0

        ui = 0
        while ui not in range(10, 100):
            try:
                print("Input even number of days (for this number it's better to be bigger):")
                ui = int(input(">>  "))
            except ValueError:
                ui = 0
        res["days"] = ui
        return res


    def _ShowPlayerCurrentMatch(self):
        res = self._league.GetCurrentMatchByClubId(self._players_club)[0]
        if res:
            print("Your match is")
            print("  {0:s} VS {1:s}".format(res[0], res[1]))
        else:
            print("You have no upcoming matches.")

    def _PrintStandings(self, row_list):
        for row in row_list:
            if row[0]:
                print(" +{0:20s} {1:2d}".format(row[1], row[2]))
            else:
                print("  {0:20s} {1:2d}".format(row[1], row[2]))

    def _ShowCurrentStandings(self, tokens):
        standings = []
        if len(tokens) == 1 or tokens[1] == "l":
            standings = self._league.GetCurrentLeagueStandings()
        elif len(tokens) == 2 or (tokens[1] == "div" and tokens[2] == "my"):
            standings = self._league.GetCurrentStandingsInMyDiv()
        elif tokens[1] == "div" and tokens[2] == "all":
            standings = self._league.GetCurrentDivStandings()
            for table in standings:
                self._PrintStandings(table)
                print()
            return PROCESS_INPUT_CODES.DEFAULT

        self._PrintStandings(standings)
        return PROCESS_INPUT_CODES.DEFAULT


    def _ProcessShowCommand(self):
        print("Day:", self._league.current_day)
        if self._league.current_matches:
            print("Upcoming matches:")
            for match in self._league.current_matches:
                print("  {0:s} VS {1:s}".format(match[2], match[3]))
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
                print("  {0:s} VS {1:s} {2:d}:{3:d}".format( match[2], match[3], match[4], match[5] ) )
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
            return self._ShowCurrentStandings(tokens)
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

    def _ProcessEndOfSeason(self, tokens):
        print("\nThe season is over.\n")
        self._ShowCurrentStandings(tokens)

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
                if self._ProcessEndOfSeason(["cs"]) == PROCESS_INPUT_CODES.HAS_TO_EXIT:
                    have_to_exit = True
                else:
                    have_to_exit = False


if __name__ == "__main__":
    game = JGame()
    game.PlayTextGame()
