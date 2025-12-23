"""
Created May 20, 2024

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.layout import make_default_layout


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        layout, anchor_layout = make_default_layout("Legends of the Courts")

        new_story_button = Button(
            text="New Story",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        new_story_button.bind(on_press=self.show_story)
        layout.add_widget(new_story_button)

        continue_story_button = Button(
            text="Continue Story",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        continue_story_button.bind(on_press=_continue_story)
        layout.add_widget(continue_story_button)

        credits_button = Button(
            text="Credits",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        credits_button.bind(on_press=self.show_credits)
        layout.add_widget(credits_button)

        exit_button = Button(
            text="Exit",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        exit_button.bind(on_press=self.exit_app)
        layout.add_widget(exit_button)

        self.add_widget(anchor_layout)

    @staticmethod
    def show_story(_):
        GameContext.new_context()
        App.get_running_app().switch_to_story_name()

    def show_credits(self, instance):
        print("Credits button pressed")
        # Here you could switch to a credits screen or display credits information

    @staticmethod
    def exit_app(_):
        App.get_running_app().stop()

def _continue_story(_):
    GameContext.new_context()
    App.get_running_app().switch_to_load_story()
