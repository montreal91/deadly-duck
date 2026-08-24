"""
Created December 23, 2025

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from client.widgets.factories import make_label

_TITLE_HEIGHT = 32
_ROW_HEIGHT = 26
_TITLE_FONT_SIZE = 24
_ROW_FONT_SIZE = 20


class PlayerDetailsWidget:
    def __init__(self):
        self._root = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=4)
        self._root.bind(minimum_height=self._root.setter("height"))
        self._wrapper = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(4 * _ROW_HEIGHT),
        )
        self._left_col = BoxLayout(orientation="vertical")
        self._right_col = BoxLayout(orientation="vertical")

        self._player_name_label = _make_detail_label(
            "Placeholder",
            font_size=_TITLE_FONT_SIZE,
            height=_TITLE_HEIGHT,
        )
        self._player_name_label.markup = True
        self._root.add_widget(self._player_name_label)

        self._left_col.add_widget(_make_detail_label("Age:"))
        self._left_col.add_widget(_make_detail_label("Level:"))
        self._left_col.add_widget(_make_detail_label("Technique:"))
        self._left_col.add_widget(_make_detail_label("Endurance:"))

        self._age_value_label = _make_detail_label("Placeholder")
        self._right_col.add_widget(self._age_value_label)

        self._level_value_label = _make_detail_label("Placeholder")
        self._right_col.add_widget(self._level_value_label)

        self._technique_value_label = _make_detail_label("Placeholder")
        self._right_col.add_widget(self._technique_value_label)

        self._endurance_value_label = _make_detail_label("Placeholder")
        self._right_col.add_widget(self._endurance_value_label)

        self._root.add_widget(self._wrapper)

        self._wrapper.add_widget(self._left_col)
        self._wrapper.add_widget(self._right_col)

    @property
    def widget(self):
        return self._root

    def update(self, player_info):
        if player_info is None:
            raise Exception("player_info should not be None")

        self._player_name_label.text = f"[b]{player_info.name}[/b]"
        self._technique_value_label.text = str(player_info.technique)
        self._endurance_value_label.text = str(player_info.endurance)
        self._age_value_label.text = str(player_info.age)
        self._level_value_label.text = str(player_info.level)


def _make_detail_label(text, font_size=_ROW_FONT_SIZE, height=_ROW_HEIGHT):
    label = make_label(text, font_size=font_size)
    label.size_hint_x = 1
    label.height = dp(height)
    label.halign = "left"
    label.valign = "middle"
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label
