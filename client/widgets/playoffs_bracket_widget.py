"""
Created August 17, 2026

@author montreal91
"""
from collections import defaultdict

from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


_SERIES_HEIGHT = dp(78)
_ROUND_TITLE_HEIGHT = dp(32)
_TEAM_NAME_WIDTH = dp(130)
_SCORE_WIDTH = dp(28)
_CONNECTOR_WIDTH = dp(8)


class PlayoffsBracketWidget:
    def __init__(self):
        self._standings = None
        self._root = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(8), dp(8)),
            spacing=dp(4),
            height=dp(750),
        )
        self._root.bind(size=self._root.setter("size"))

        self._title = make_label(text="Playoffs Bracket", font_size=35)
        self._root.add_widget(self._title)
        self._root.add_widget(Widget())

    @property
    def widget(self):
        return self._root

    def update(self, standings):
        self._standings = standings
        self._root.clear_widgets()
        self._root.add_widget(self._title)

        if not standings.rows:
            self._root.add_widget(Widget())
            return

        bracket = BoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            size_hint=(1, 1),
        )

        grouped_rows = list(_group_by_round(standings.rows))
        last_round = grouped_rows[-1][0]

        for round_number, rows in grouped_rows:
            bracket.add_widget(_make_round_column(
                round_number,
                rows,
                has_next_round=round_number < last_round,
            ))

        self._root.add_widget(bracket)


def _group_by_round(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row.round_number].append(row)

    for round_number in sorted(groups):
        yield round_number, groups[round_number]


def _make_round_column(round_number, rows, has_next_round):
    column = BoxLayout(
        orientation="vertical",
        spacing=dp(10),
        size_hint=(1, 1),
    )

    column.add_widget(_make_round_title(round_number))

    body = BoxLayout(
        orientation="vertical",
        spacing=_round_spacing(round_number),
        size_hint=(1, 1),
    )

    body.add_widget(_make_spacer(_round_spacing(round_number) // 2))
    for row in rows:
        body.add_widget(_make_series(row, has_next_round))
    body.add_widget(Widget())

    column.add_widget(body)
    return column


def _make_round_title(round_number):
    title = Label(
        text=f"Round {round_number}",
        font_size=24,
        halign="center",
        valign="middle",
        size_hint=(1, None),
        height=_ROUND_TITLE_HEIGHT,
    )
    title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return title


def _make_series(series, has_next_round):
    block = BoxLayout(
        orientation="vertical",
        size_hint=(1, None),
        height=_SERIES_HEIGHT,
        padding=(dp(6), dp(4)),
        spacing=dp(2),
    )

    with block.canvas.before:
        if series.contains_manager_club:
            block._bg_color = Color(rgba=(.2, .2, .2, 1))
        else:
            block._bg_color = Color(rgba=(.08, .08, .08, 1))
        block._bg_rect = Rectangle(pos=block.pos, size=block.size)

    with block.canvas.after:
        block._border_color = Color(rgba=(.45, .45, .45, 1))
        block._border_line = Line(rectangle=(
            block.x,
            block.y,
            block.width,
            block.height,
        ))
        block._connector_line = Line(width=1.1)

    block._has_next_round = has_next_round
    block.bind(pos=_update_series_canvas, size=_update_series_canvas)

    block.add_widget(_make_team_row(series.top_club_name, series.top_score))
    block.add_widget(_make_team_row(series.bottom_club_name, series.bottom_score))
    return block


def _make_team_row(club_name, score):
    row = BoxLayout(orientation="horizontal", size_hint=(1, 1))
    row.add_widget(_make_team_name_cell(club_name))
    row.add_widget(_make_score_cell(str(score)))
    return row


def _make_team_name_cell(value):
    lbl = Label(
        text=value,
        font_size=18,
        halign="left",
        valign="middle",
        size_hint_x=1,
        width=_TEAM_NAME_WIDTH,
        shorten=True,
        shorten_from="right",
    )
    lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return lbl


def _make_score_cell(value):
    lbl = Label(
        text=value,
        font_size=18,
        halign="center",
        valign="middle",
        size_hint_x=None,
        width=_SCORE_WIDTH,
    )
    lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return lbl


def _make_spacer(height):
    return Widget(size_hint_y=None, height=height)


def _round_spacing(round_number):
    return dp(18 * 2 ** (round_number - 1))


def _update_series_canvas(block, *_):
    block._bg_rect.pos = block.pos
    block._bg_rect.size = block.size
    block._border_line.rectangle = (
        block.x,
        block.y,
        block.width,
        block.height,
    )
    if block._has_next_round:
        block._connector_line.points = (
            block.right,
            block.center_y,
            block.right + _CONNECTOR_WIDTH,
            block.center_y,
        )
    else:
        block._connector_line.points = ()
