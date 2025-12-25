"""
Created December 23, 2025

@author montreal91
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


class PlayerDetailsWidget:
    def __init__(self):
        self._root = BoxLayout(orientation="vertical")
        self._wrapper = BoxLayout(orientation="horizontal")
        self._left_col = BoxLayout(orientation="vertical")
        self._right_col = BoxLayout(orientation="vertical")

        self._player_name_label = make_label("Placeholder")
        self._root.add_widget(self._player_name_label)


        self._left_col.add_widget(make_label("Level:", font_size=25))
        self._left_col.add_widget(make_label("Technique:", font_size=25))
        self._left_col.add_widget(make_label("Endurance:", font_size=25))
        self._left_col.add_widget(make_label("Age:", font_size=25))
        self._left_col.add_widget(make_label("Speciality:", font_size=25))

        self._level_value_label = make_label("Placeholder", font_size=25)
        self._right_col.add_widget(self._level_value_label)

        self._technique_value_label = make_label("Placeholder", font_size=25)
        self._right_col.add_widget(self._technique_value_label)

        self._endurance_value_label = make_label("Placeholder",font_size=25)
        self._right_col.add_widget(self._endurance_value_label)

        self._age_value_label = make_label("Placeholder", font_size=25)
        self._right_col.add_widget(self._age_value_label)

        self._speciality_value_label = make_label("Placeholder", font_size=25)
        self._right_col.add_widget(self._speciality_value_label)

        self._root.add_widget(self._wrapper)

        self._left_col.add_widget(make_label(""))
        self._right_col.add_widget(make_label(""))

        self._left_col.add_widget(Widget())
        self._right_col.add_widget(Widget())

        self._wrapper.add_widget(self._left_col)
        self._wrapper.add_widget(self._right_col)

    @property
    def widget(self):
        return self._root

    def update(self, player_info):
        if player_info is None:
            raise Exception("player_info should not be None")

        self._player_name_label.text = player_info.name
        self._technique_value_label.text = str(player_info.technique)
        self._endurance_value_label.text = str(player_info.endurance)
        self._age_value_label.text = str(player_info.age)
        self._level_value_label.text = str(player_info.level)
        self._speciality_value_label.text = player_info.speciality
