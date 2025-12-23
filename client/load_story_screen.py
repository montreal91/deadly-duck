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


class LoadStoryScreen(Screen):
    def __init__(self, **kwargs):
        super(LoadStoryScreen, self).__init__(**kwargs)

        self._game_service = get_application_context().game_service

        self._saved_games_buttons = []
        self._selected_save = None

        self._layout, root = make_default_layout("Continue Story")

        self._filler_label = Label()
        self._layout.add_widget(self._filler_label)

        self._continue_button = Button(text="Continue", size_hint=(None, None), size=button_size)
        self._continue_button.bind(on_press=self._on_continue)
        self._layout.add_widget(self._continue_button)

        self._back_button = Button(text="Back", font_size=30, size_hint=(None, None), size=button_size)
        self._back_button.bind(on_press=_back_to_main_screen)
        self._layout.add_widget(self._back_button)

        self.add_widget(root)

    def update_saved_games(self):
        self._undo_previous_buttons()
        self._saved_games_buttons = []
        self._selected_save = None
        self._continue_button.disabled = True

        stories = self._game_service.get_saved_games().names
        for story in stories:
            button = self._make_load_game_button(story)
            self._layout.add_widget(button)
            self._saved_games_buttons.append(button)

        self._layout.add_widget(self._filler_label)
        self._layout.add_widget(self._continue_button)
        self._layout.add_widget(self._back_button)

    def _undo_previous_buttons(self):
        for button in self._saved_games_buttons:
            button.unbind(on_press=self._on_select)
            self._layout.remove_widget(button)

        self._layout.remove_widget(self._filler_label)
        self._layout.remove_widget(self._continue_button)
        self._layout.remove_widget(self._back_button)

    def _make_load_game_button(self, game_name):
        button = ToggleButton(
            text=game_name,
            group="games",
            size_hint=(None, None),
            size=button_size
        )
        button.game_name = game_name
        button.bind(on_press=self._on_select)
        return button

    def _on_select(self, instance):
        print(instance.game_name)
        self._selected_save = instance.game_name
        self._continue_button.disabled = False

    def _on_continue(self, _):
        print(self._selected_save)

        if self._selected_save is None:
            print("No game is selected")
            return

        GameContext.get_instance().game_name = self._selected_save
        GameContext.get_instance().club_id = self._game_service.get_manager_club_id(
            self._selected_save
        )

        App.get_running_app().start_game()


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)
