"""
Created December 24, 2025

@author montreal91
"""
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.factories import make_label

_POS_WIDTH = 0.12
_CLUB_WIDTH = 0.42
_MATCHES_WIDTH = 0.20
_SETS_WIDTH = 0.12
_GAMES_WIDTH = 0.14
_ROW_HEIGHT = dp(26)
_HEADER_HEIGHT = dp(28)
_HEADER_GAP = dp(4)


class StandingsTableWidget:
    def __init__(self):
        self._root = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=(dp(6), dp(4)),
            spacing=dp(2),
        )

        self._title = make_label(text="Standings Table", font_size=28)
        self._root.add_widget(self._title)

        self._table_header = _make_table_header()
        self._root.add_widget(self._table_header)
        self._header_gap = Widget(size_hint_y=None, height=_HEADER_GAP)

    @property
    def widget(self):
        return self._root

    def update(self, standings):
        self._root.clear_widgets()

        self._root.add_widget(self._title)
        self._root.add_widget(self._table_header)
        self._root.add_widget(self._header_gap)

        for row in standings.rows:
            self._root.add_widget(_make_row(row))

        self._root.add_widget(Widget())


def _make_table_header():
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=_HEADER_HEIGHT)

    row.add_widget(_make_cell("[b]Pos.[/b]", align="left", width=_POS_WIDTH, is_header=True))
    row.add_widget(_make_cell("[b]Club[/b]", align="center", width=_CLUB_WIDTH, is_header=True))
    row.add_widget(_make_cell("[b]Matches[/b]", align="center", width=_MATCHES_WIDTH, is_header=True))
    row.add_widget(_make_cell("[b]Sets[/b]", align="center", width=_SETS_WIDTH, is_header=True))
    row.add_widget(_make_cell("[b]Games[/b]", align="center", width=_GAMES_WIDTH, is_header=True))

    return row


def _make_cell(value, width, align, is_header=False):
    lbl = Label(
        text=value,
        markup=is_header,
        halign=align,
        valign="middle",
        size_hint_x=width,
    )
    lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return lbl


def _make_row(standings_row):
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=_ROW_HEIGHT)

    if standings_row.club_id == GameContext.get_instance().club_id:
        with row.canvas.before:
            row._bg_color = Color(rgba=(.2, .2, .2, 1))
            row._bg_rect = Rectangle(pos=row.pos, size=row.size)
        row.bind(pos=_update_bg, size=_update_bg)

    pos = _make_cell(str(standings_row.pos), width=_POS_WIDTH, align="left")
    row.add_widget(pos)

    club = _make_cell(str(standings_row.club_name), width=_CLUB_WIDTH, align="left")
    row.add_widget(club)

    matches = _make_cell(str(standings_row.matches), width=_MATCHES_WIDTH, align="center")
    row.add_widget(matches)

    sets = _make_cell(str(standings_row.sets), width=_SETS_WIDTH, align="center")
    row.add_widget(sets)

    games = _make_cell(str(standings_row.games), width=_GAMES_WIDTH, align="center")
    row.add_widget(games)

    return row


def _update_bg(self, *_):
    self._bg_rect.pos = self.pos
    self._bg_rect.size = self.size
