"""
Created December 21, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.new_game_context import GameContext
from client.widgets.layout import make_default_layouts
from configuration.application_context import get_application_context


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

        self._game_service = get_application_context().game_service
        self._game_id = None
        self._club_id = None

        self._layout, root = make_default_layouts("")

        back_button = Button(text="Back", font_size=30, size_hint=(None, None), size=button_size)
        back_button.bind(on_press=self._back_to_main_screen)
        self._layout.add_widget(back_button)

        self.add_widget(root)

    def init_game_data(self):
        self._game_id = GameContext.get_instance().game_name
        self._club_id = GameContext.get_instance().club_id

    def update(self):
        info = self._game_service.get_main_screen_info(self._game_id, self._club_id)
        self._layout.title_label.text = info.club_name


    def _back_to_main_screen(self, _):
        self._game_service.save_game(self._game_id)

        App.get_running_app().switch_to_main(None)
