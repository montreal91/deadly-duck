"""
Created August 17, 2026

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from client.widgets.factories import make_label


class PlayoffsBracketWidget:
    def __init__(self):
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

    def update(self, _standings):
        self._root.clear_widgets()
        self._root.add_widget(self._title)
        self._root.add_widget(Widget())
