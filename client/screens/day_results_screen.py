"""
Created December 24, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.widgets.layout import make_default_layout


class DayResultsScreen(Screen):
    def __init__(self, **kwargs):
        super(DayResultsScreen, self).__init__(**kwargs)

        layout, anchor_layout = make_default_layout("Results")

        continue_button = Button(
            text="continue",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        continue_button.bind(on_press=_on_continue)
        layout.add_widget(continue_button)

        self.add_widget(anchor_layout)

def _on_continue(_):
    App.get_running_app().return_to_game()
