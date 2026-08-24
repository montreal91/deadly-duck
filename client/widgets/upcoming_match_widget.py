"""
Created December 24, 2025

@author montreal91
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


class UpcomingMatchWidget:
    def __init__(self):
        self._root = BoxLayout(orientation="vertical", size_hint=(1, None))
        self._root.bind(minimum_height=self._root.setter("height"))

        self._teaser_label = _make_wrapped_label(font_size=20)
        self._home_away_label = _make_wrapped_label(font_size=25)
        self._opponent_club_label = _make_wrapped_label(font_size=40)

    @property
    def root(self):
        return self._root

    def update(self, opp=None):
        self._root.clear_widgets()

        if opp is None:
            self._teaser_label.text = "No matches today. Chill."
            self._home_away_label.text = " "
            self._opponent_club_label.text = " "
        else:
            self._teaser_label.text = "Upcoming match"
            self._home_away_label.text = opp.home_away
            self._opponent_club_label.text = opp.opponent_club_name

        self._root.add_widget(self._teaser_label)
        self._root.add_widget(self._opponent_club_label)
        self._root.add_widget(self._home_away_label)
        self._root.add_widget(Widget())


def _make_wrapped_label(font_size):
    label = make_label(text=" ", font_size=font_size)
    label.size_hint_x = 1
    label.halign = "left"
    label.valign = "middle"
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label
