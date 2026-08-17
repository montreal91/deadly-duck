"""
Created December 22, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.alphanumeric_text_input import AlphanumericTextInput
from client.widgets.layout import make_default_layout
from configuration.application_context import get_application_context
from core.ports.inbound.commands.create_new_game import CreateNewGameCommand


class StoryNameScreen(Screen):
    def __init__(self, **kwargs):
        super(StoryNameScreen, self).__init__(**kwargs)

        layout, root = make_default_layout("Story Name")

        ac = get_application_context()
        self._create_new_game_command = ac.create_game_command_handler

        self._text_input = AlphanumericTextInput(
            hint_text="Type something here",
            multiline=False,
            size_hint=(None, None),
            size=button_size,
        )

        layout.add_widget(self._text_input)
        self._error_label = Label()
        layout.add_widget(self._error_label)

        layout.add_widget(Label())

        continue_button = Button(text="Continue", font_size=30, size_hint=(None, None), size=button_size)
        continue_button.bind(on_press=self._continue)
        layout.add_widget(continue_button)

        back_button = Button(text="Back", font_size=30, size_hint=(None, None), size=button_size)
        back_button.bind(on_press=_back_to_main_screen)
        layout.add_widget(back_button)

        self.add_widget(root)

    def update(self):
        self._text_input.text = ""

    def _continue(self, _):
        if len(self._text_input.text) < 3:
            self._error_label.text = "Please type at least 3 characters"
            return

        GameContext.get_instance().game_name = self._create_new_game_command(
            CreateNewGameCommand(self._text_input.text)
        ).game_id

        App.get_running_app().switch_to_club_selection()


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)
