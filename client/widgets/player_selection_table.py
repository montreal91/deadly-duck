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

_DEFAULT_COL_WIDTH = 100


class PlayerSelectionTable:
    def __init__(self):
        self._root = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(8), dp(8)),
            spacing=dp(4)
        )
        self._selected_player_id = None

        self._header = _PlayerTableHeader()
        self._root.add_widget(self._header.widget)
        self._root.bind(size=self._root.setter("size"))

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

    def _make_select_player_button(self, player_id):
        button = ToggleButton(
            text="Select",
            group="players",
            size_hint=(None, None),
            size=(100, 35)
        )
        button.player_id = player_id
        button.bind(on_press=self._on_select)
        return button

    def _make_table_row(self, pos, player, selected=False):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))

        if selected:
            with row.canvas.before:
                row._bg_color = Color(rgba=(.2, .2, .2, 1))
                row._bg_rect = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=_update_bg, size=_update_bg)

        row.add_widget(_make_cell(str(pos)))
        row.add_widget(_make_cell(player.name))
        row.add_widget(_make_cell(str(player.level)))
        row.add_widget(_make_cell(
            f"{player.actual_technique} / {player.technique}"
        ))
        row.add_widget(_make_cell(
            f"{player.current_stamina} / {player.maximum_stamina}"
        ))
        row.add_widget(_make_cell(str(player.exhaustion)))
        row.add_widget(_make_cell(player.speciality))

        row.add_widget(self._make_select_player_button(player.player_id))

        return row

    def _on_select(self, instance):
        self._selected_player_id = instance.player_id


class _PlayerTableHeader:
    def __init__(self):
        self._root = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))

        cols = (
            "#",
            "Name",
            "Level",
            "Technique",
            "Stamina",
            "Exhaustion",
            "Speciality",
            ""
        )

        for title in cols:
            lbl = Label(
                text=f"[b]{title}[/b]",
                markup=True,
                halign="center",
                valign="middle",
                size_hint_x=None,
                width=dp(_DEFAULT_COL_WIDTH)
            )
            lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            self._root.add_widget(lbl)

    @property
    def widget(self):
        return self._root


def _make_cell(value):
    return Label(
        text=value,
        markup=True,
        halign="left",
        valign="middle",
        size_hint_x=None,
        width=dp(_DEFAULT_COL_WIDTH),
    )


def _update_bg(self, *_):
    self._bg_rect.pos = self.pos
    self._bg_rect.size = self.size
