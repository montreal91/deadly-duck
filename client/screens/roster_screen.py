"""
Created December 26, 2025

@author montreal91
"""
from kivy.uix.screenmanager import Screen

from client.widgets.layout import make_three_column_layout


class RosterScreen(Screen):
    def __init__(self, **kwargs):
        super(RosterScreen, self).__init__(**kwargs)

        self._layout = make_three_column_layout(
            title_text="Roster",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3
        )

        self.add_widget(self._layout.root)
