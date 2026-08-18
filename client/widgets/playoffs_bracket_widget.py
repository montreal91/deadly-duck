"""
Created August 17, 2026

@author montreal91
"""
from collections import defaultdict

from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


_SERIES_HEIGHT = dp(78)
_FIRST_ROUND_SERIES_GAP = dp(18)
_ROUND_TITLE_HEIGHT = dp(32)
_TEAM_NAME_WIDTH = dp(130)
_SCORE_WIDTH = dp(28)
_ROUND_GAP = dp(16)
_TITLE_BODY_GAP = dp(10)
_ROUND_TITLES = {
    1: "Quarterfinals",
    2: "Semifinals",
    3: "Final",
}


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

        grouped_rows = list(_group_by_round(standings.rows))
        last_round = grouped_rows[-1][0]

        self._root.add_widget(_PlayoffBracketLayout(grouped_rows, last_round))


def _group_by_round(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row.round_number].append(row)

    for round_number in sorted(groups):
        yield round_number, groups[round_number]


class _PlayoffBracketLayout(FloatLayout):
    def __init__(self, grouped_rows, last_round, **kwargs):
        super(_PlayoffBracketLayout, self).__init__(**kwargs)
        self._grouped_rows = grouped_rows
        self._last_round = last_round
        self._series_widgets = {}
        self.bind(pos=self._layout_bracket, size=self._layout_bracket)
        Clock.schedule_once(self._layout_bracket, 0)

    def _layout_bracket(self, *_):
        self.clear_widgets()
        self.canvas.before.clear()
        self._series_widgets = {}

        if not self._grouped_rows or self.width <= 0 or self.height <= 0:
            return

        round_count = len(self._grouped_rows)
        series_width = (
            self.width - _ROUND_GAP * (round_count - 1)
        ) / round_count
        body_top = self.top - _ROUND_TITLE_HEIGHT - _TITLE_BODY_GAP
        body_height = body_top - self.y

        if body_height <= _SERIES_HEIGHT:
            return

        for round_index, (round_number, rows) in enumerate(self._grouped_rows):
            x = self.x + round_index * (series_width + _ROUND_GAP)
            self.add_widget(_make_round_title(
                round_number,
                pos=(x, body_top + _TITLE_BODY_GAP),
                width=series_width,
            ))

            centers = _series_centers(round_number, len(rows), body_height)
            for row_index, row in enumerate(rows):
                center_y = self.y + centers[row_index]
                series_widget = _make_series(
                    row,
                    pos=(x, center_y - _SERIES_HEIGHT / 2),
                    size=(series_width, _SERIES_HEIGHT),
                )
                self._series_widgets[(round_number, row_index)] = series_widget
                self.add_widget(series_widget)

        self._draw_connectors()

    def _draw_connectors(self):
        with self.canvas.before:
            Color(rgba=(.45, .45, .45, 1))
            for round_number, rows in self._grouped_rows[:-1]:
                for row_index, _ in enumerate(rows):
                    source = self._series_widgets[(round_number, row_index)]
                    target_key = (round_number + 1, row_index // 2)
                    target = self._series_widgets.get(target_key)

                    if target is None:
                        continue

                    elbow_x = source.right + _ROUND_GAP / 2
                    Line(points=(
                        source.right,
                        source.center_y,
                        elbow_x,
                        source.center_y,
                        elbow_x,
                        target.center_y,
                        target.x,
                        target.center_y,
                    ), width=1.1)


def _make_round_title(round_number, pos=None, width=None):
    title = Label(
        text=_ROUND_TITLES.get(round_number, f"Round {round_number}"),
        font_size=24,
        halign="center",
        valign="middle",
        size_hint=(None, None),
        width=width,
        height=_ROUND_TITLE_HEIGHT,
    )
    if pos is not None:
        title.pos = pos
    title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return title


def _make_series(series, pos=None, size=None):
    block = BoxLayout(
        orientation="vertical",
        size_hint=(None, None),
        padding=(dp(6), dp(4)),
        spacing=dp(2),
    )
    if pos is not None:
        block.pos = pos
    if size is not None:
        block.size = size

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


def _series_centers(round_number, series_count, body_height):
    first_round_step = _SERIES_HEIGHT + _FIRST_ROUND_SERIES_GAP
    first_round_count = series_count * 2 ** (round_number - 1)
    first_round_total_height = (
        first_round_count * _SERIES_HEIGHT
        + (first_round_count - 1) * _FIRST_ROUND_SERIES_GAP
    )
    bottom_offset = max((body_height - first_round_total_height) / 2, 0)
    group_size = 2 ** (round_number - 1)

    return [
        (
            bottom_offset
            + (index * group_size + (group_size - 1) / 2) * first_round_step
            + _SERIES_HEIGHT / 2
        )
        for index in range(series_count)
    ]


def _update_series_canvas(block, *_):
    block._bg_rect.pos = block.pos
    block._bg_rect.size = block.size
    block._border_line.rectangle = (
        block.x,
        block.y,
        block.width,
        block.height,
    )
