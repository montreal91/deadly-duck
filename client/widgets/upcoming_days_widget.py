"""
Created August 24, 2026

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from client.widgets.factories import make_label

_MAX_DAYS = 6
_DAY_FONT_SIZE = 22
_HOME_AWAY_FONT_SIZE = 18
_DAY_LABEL_HEIGHT = 26
_HOME_AWAY_LABEL_HEIGHT = 20
_DAY_SPACER_HEIGHT = 6


class UpcomingDaysWidget:
    def __init__(self):
        self._root = BoxLayout(
            orientation="vertical",
            spacing=5,
            size_hint=(1, None),
        )
        self._root.bind(minimum_height=self._root.setter("height"))

    @property
    def root(self):
        return self._root

    def update(self, upcoming_days):
        self._root.clear_widgets()

        for day in upcoming_days[1:_MAX_DAYS]:
            self._root.add_widget(_make_day_row(day))


def _make_day_row(day):
    row = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=2)
    row.bind(minimum_height=row.setter("height"))

    day_label = _make_wrapped_label(
        text=_make_day_text(day),
        font_size=_DAY_FONT_SIZE,
        height=_DAY_LABEL_HEIGHT,
        markup=True,
    )

    row.add_widget(day_label)

    if day.match:
        row.add_widget(_make_wrapped_label(
            text=_make_home_away_text(day.match),
            font_size=_HOME_AWAY_FONT_SIZE,
            height=_HOME_AWAY_LABEL_HEIGHT,
        ))

    row.add_widget(Widget(size_hint_y=None, height=dp(_DAY_SPACER_HEIGHT)))

    return row


def _make_day_text(day) -> str:
    opp = day.match.opponent_club_name if day.match else "[i]Day Off[/i]"
    return f"{day.day}: {opp}"

def _make_home_away_text(match):
    home_away = match.home_away
    return f"({home_away})"


def _make_wrapped_label(text, font_size, height, markup=False):
    label = make_label(text=text, font_size=font_size)
    label.markup = markup
    label.size_hint_x = 1
    label.height = dp(height)
    label.halign = "left"
    label.valign = "middle"
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label
