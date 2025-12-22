"""
Created May 20, 2024

@author montreal91
"""
import json

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton

from client.constants import button_size
from client.new_game_context import GameContext
from client.widgets.layout import make_default_layouts
from configuration.application_context import get_application_context


class ClubSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super(ClubSelectionScreen, self).__init__(**kwargs)
        self._current_id = None
        self._game_service = get_application_context().game_service

        layout, root = make_default_layouts("Select Your Club")

        layout.add_widget(Label())
        self._club_buttons = []

        for i, text in enumerate(_get_club_names()):
            button = ToggleButton(text=text, group="clubs", size_hint=(None, None), size=button_size)
            button.bind(on_press=self._on_select)
            button.club_id = i
            layout.add_widget(button)
            self._club_buttons.append(button)

        layout.add_widget(Label())

        self._start_button = Button(
            text="Start New Story",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        self._start_button.disabled = True
        self._start_button.bind(on_press=self._start_new_story)
        layout.add_widget(self._start_button)

        back_button = Button(
            text="Back to Main Menu",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_back_to_main_screen)
        layout.add_widget(back_button)

        self.add_widget(root)

    def cleanup(self):
        for button in self._club_buttons:
            button.state = "normal"

        self._start_button.disabled = True

    def _on_select(self, btn):
        if btn.state == "down":
            self._current_id = btn.club_id
            self._start_button.disabled = False

    def _start_new_story(self, _):
        context = GameContext.get_instance()
        context.club_id = self._current_id

        self._game_service.create_new_game(
            game_id=context.game_name,
            manager_club_id=context.club_id
        )

        App.get_running_app().start_game()


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)


def _get_club_names():
    with open("data/clubs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return [obj["name"] for obj in data]
