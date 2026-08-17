"""
Created December 22, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.layout import make_default_layout
from configuration.application_context import get_application_context
from core.ports.inbound.commands.select_club import SelectClubCommand
from core.queries.club_selection_screen_query import ClubSelectionScreenQuery


class ClubSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super(ClubSelectionScreen, self).__init__(**kwargs)
        self._current_id = None
        self._game_service = get_application_context().game_service
        self._query_handler = get_application_context().select_club_screen_query_handler
        self._command_handler = get_application_context().select_club_command_handler

        self._layout, root = make_default_layout("Select Your Club")

        self._layout.add_widget(Label())
        self._club_buttons = []
        self._layout.add_widget(Label())

        self._start_button = Button(
            text="Start New Story",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        self._start_button.disabled = True
        self._start_button.bind(on_press=self._start_new_story)
        self._layout.add_widget(self._start_button)

        back_button = Button(
            text="Back to Main Menu",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_back_to_main_screen)
        self._layout.add_widget(back_button)

        self.add_widget(root)

    def update(self):
        for btn in self._club_buttons:
            self._layout.remove_widget(btn)

        self._club_buttons = []

        query = ClubSelectionScreenQuery(game_id=GameContext.get_instance().game_name)

        for club in self._query_handler(query).club_infos:
            button = ToggleButton(
                text=club.club_name,
                group="clubs",
                size_hint=(None, None),
                size=button_size
            )
            button.bind(on_press=self._on_select)
            button.club_id = club.club_id
            self._layout.add_widget(button)
            self._club_buttons.append(button)

        self._start_button.disabled = True

    def _on_select(self, btn):
        if btn.state == "down":
            self._current_id = btn.club_id
            self._start_button.disabled = False

    def _start_new_story(self, _):
        context = GameContext.get_instance()
        context.club_id = self._current_id

        command = SelectClubCommand(
            game_id=context.game_name,
            club_id=context.club_id,
        )

        self._command_handler(command)
        App.get_running_app().start_game()


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)
