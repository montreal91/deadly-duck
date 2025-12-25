"""
Created December 24, 2025

@author montreal91
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


class UpcomingMatchWidget:
    def __init__(self):
        self._root = BoxLayout(orientation="vertical")

        self._teaser_label = make_label(text = " ", font_size=20)
        self._opponent_club_label = make_label(text = " ", font_size=40)

    @property
    def root(self):
        return self._root

    def update(self, opp=None):
        self._root.clear_widgets()

        if opp is None:
            self._teaser_label.text = "No matches today. Chill."
            self._opponent_club_label.text = " "
        else:
            self._teaser_label.text = "Upcoming match"
            self._opponent_club_label.text = opp.opponent_club_name

        self._root.add_widget(self._teaser_label)
        self._root.add_widget(self._opponent_club_label)
        self._root.add_widget(Widget())
