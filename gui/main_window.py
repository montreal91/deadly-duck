from random import shuffle
# from PySide.QtCore                      import Slot
from PySide.QtGui                       import QWidget

from gui.widgets.main_window_ui         import Ui_JMainWindow

from club import JClub
from league import JLeague

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

class JMainWindow(QWidget):
    def __init__(self):
        super(JMainWindow, self).__init__()
        self.widget = Ui_JMainWindow()
        self.widget.setupUi(self)

    def CreateLeague(self, param_dict):
        self._league = JLeague(
            days=param_dict["days"],
            divisions=param_dict["divs"],
            indiv_matches=param_dict["in_div_games"],
            exdiv_matches=param_dict["out_div_games"]
        )
        tennis_players      = 4
        t_players_list      = [i+1 for i in range(len(club_names) * tennis_players)]
        shuffle(t_players_list)
        for i in range(len(club_names)):
            if i + 1 == 1:
                club = JClub(club_id=i+1, name=club_names[i], playable=True)
            else:
                club = JClub(club_id=i+1, name=club_names[i], playable=False)

            for j in range(tennis_players):
                club.AddPlayer(t_players_list.pop())
            self._league.AddClub(club)
        self._league.CreateSchedule()
