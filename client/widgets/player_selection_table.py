"""
Created December 23, 2025

@author montreal91
"""
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton

_PLAYER_ID_COL_WIDTH = 0.06
_PLAYER_NAME_COL_WIDTH = 0.26
_SMALL_COL_WIDTH = 0.08
_DEFAULT_COL_WIDTH = 0.13
_ACTION_COL_WIDTH = 0.10
_TABLE_PADDING = 8
_ROW_HEIGHT = 34


class PlayerSelectionTable:
    def __init__(self):
        self._root = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(_TABLE_PADDING), dp(_TABLE_PADDING)),
            spacing=dp(4),
            size_hint_x=1,
        )
        self._selected_player_id = None

        self._header = _PlayerTableHeader()
        self._root.add_widget(self._header.widget)
        self._root.bind(minimum_height=self._root.setter("height"))

    @property
    def widget(self):
        return self._root

    @property
    def selected_player_id(self):
        return self._selected_player_id

    def update(self, players):
        self._selected_player_id = None
        self._root.clear_widgets()
        self._root.add_widget(self._header.widget)

        for pos, player in enumerate(players):
            self._root.add_widget(self._make_table_row(pos, player, player.is_selected))

    def _make_select_player_button(self, player_id, selected=False):
        button = ToggleButton(
            text="Select",
            group="players",
            size_hint=(1, None),
            height=dp(_ROW_HEIGHT),
            state="down" if selected else "normal",
        )
        button.player_id = player_id
        button.bind(on_press=self._on_select)
        return button

    def _make_table_row(self, pos, player, selected=False):
        row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(_ROW_HEIGHT),
        )

        if selected:
            self._selected_player_id = player.player_id
            with row.canvas.before:
                row._bg_color = Color(rgba=(.18, .26, .34, 1))
                row._bg_rect = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=_update_bg, size=_update_bg)

        row.add_widget(_make_cell(str(pos), width=_PLAYER_ID_COL_WIDTH))
        row.add_widget(_make_cell(player.name, width=_PLAYER_NAME_COL_WIDTH))
        row.add_widget(_make_cell(str(player.age), width=_SMALL_COL_WIDTH))
        row.add_widget(_make_cell(str(player.level), width=_SMALL_COL_WIDTH))
        row.add_widget(_make_cell(
            f"{player.actual_technique} / {player.technique}"
        ))
        row.add_widget(_make_cell(
            f"{player.current_stamina} / {player.maximum_stamina}"
        ))
        row.add_widget(_make_cell(str(player.exhaustion)))

        action = self._make_select_player_button(player.player_id, selected)
        action.size_hint_x = _ACTION_COL_WIDTH
        row.add_widget(action)

        return row

    def _on_select(self, instance):
        self._selected_player_id = instance.player_id


class _PlayerTableHeader:
    def __init__(self):
        self._root = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(_ROW_HEIGHT),
        )

        cols = (
            "#",
            "Name",
            "Age",
            "Level",
            "Tech.",
            "Stamina",
            "Exh.",
            "Action"
        )

        for title in cols:
            lbl = Label(
                text=f"[b]{title}[/b]",
                markup=True,
                halign="left",
                valign="middle",
                size_hint_x=_get_col_width(title)
            )
            lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            self._root.add_widget(lbl)

    @property
    def widget(self):
        return self._root


def _make_cell(value, width=_DEFAULT_COL_WIDTH):
    cell = Label(
        text=value,
        markup=True,
        halign="left",
        valign="middle",
        size_hint_x=width,
    )
    cell.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return cell


def _get_col_width(title):
    if title == "#":
        return _PLAYER_ID_COL_WIDTH
    if title == "Name":
        return _PLAYER_NAME_COL_WIDTH
    if title in ("Age", "Level"):
        return _SMALL_COL_WIDTH
    if title == "Action":
        return _ACTION_COL_WIDTH
    return _DEFAULT_COL_WIDTH


def _update_bg(self, *_):
    self._bg_rect.pos = self.pos
    self._bg_rect.size = self.size
