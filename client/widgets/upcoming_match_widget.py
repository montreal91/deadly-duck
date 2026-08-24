"""
Created December 24, 2025

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from client.widgets.factories import make_label

_TEASER_HEIGHT = 18
_OPPONENT_HEIGHT = 42
_HOME_AWAY_HEIGHT = 22


class UpcomingMatchWidget:
    def __init__(self):
        self._root = BoxLayout(orientation="vertical", size_hint=(1, None))
        self._root.bind(minimum_height=self._root.setter("height"))

        self._teaser_label = _make_wrapped_label(
            font_size=18,
            height=_TEASER_HEIGHT,
        )
        self._home_away_label = _make_wrapped_label(
            font_size=20,
            height=_HOME_AWAY_HEIGHT,
        )
        self._opponent_club_label = _make_wrapped_label(
            font_size=30,
            height=_OPPONENT_HEIGHT,
        )

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


def _make_wrapped_label(font_size, height):
    label = make_label(text=" ", font_size=font_size)
    label.size_hint_x = 1
    label.height = dp(height)
    label.halign = "left"
    label.valign = "middle"
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label
