"""
Created December 21, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.layout import make_default_layout
from configuration.application_context import get_application_context


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

        self._info = None
        self._game_service = get_application_context().game_service
        self._game_id = None
        self._club_id = None

        self._layout, root = make_default_layout("")

        self._layout.add_widget(Label())

        self._date_label = Label(text="PlaceHolder", font_size=30, size_hint=(None, None))
        self._date_label.bind(texture_size=self._date_label.setter("size"))
        self._layout.add_widget(self._date_label)

        self._season_label = Label(text="PlaceHolder", font_size=30, size_hint=(None, None))
        self._season_label.bind(texture_size=self._season_label.setter("size"))
        self._layout.add_widget(self._season_label)

        self._current_stage_label = Label(text="PlaceHolder", font_size=30, size_hint=(None, None))
        self._current_stage_label.bind(texture_size=self._current_stage_label.setter("size"))
        self._layout.add_widget(self._current_stage_label)

        self._balance_label = Label(text="PlaceHolder", font_size=30, size_hint=(None, None))
        self._balance_label.bind(texture_size=self._balance_label.setter("size"))
        self._layout.add_widget(self._balance_label)

        self._error_label = Label(text="", font_size=20, size_hint=(None, None))
        self._error_label.bind(texture_size=self._error_label.setter("size"))
        self._error_label.color = (0.8, 0.2, 0.2, 1)
        self._layout.add_widget(self._error_label)

        self._next_button = Button(text="Next", font_size=30, size_hint=(None, None), size=button_size)
        self._next_button.bind(on_press=self._on_next)
        self._layout.add_widget(self._next_button)

        self._select_player_button = Button(
            text="Select Player",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        self._select_player_button.bind(on_press=self._on_select_player)
        self._layout.add_widget(self._select_player_button)

        self._layout.add_widget(Label())

        self._back_button = Button(text="Back", font_size=30, size_hint=(None, None), size=button_size)
        self._back_button.bind(on_press=self._back_to_main_screen)
        self._layout.add_widget(self._back_button)

        self.add_widget(root)

    def init_game_data(self):
        self._game_id = GameContext.get_instance().game_name
        self._club_id = GameContext.get_instance().club_id

    def update(self):
        info = self._game_service.get_main_screen_info(self._game_id, self._club_id)
        gui_info = self._game_service.get_main_screen_gui_info(self._game_id, self._club_id)

        self._layout.title_label.text = info.club_name
        self._date_label.text = f"Day: {gui_info.day}"
        self._season_label.text = f"Your Season: {gui_info.season}"
        self._current_stage_label.text = f"Current Stage: {gui_info.current_competition}"
        self._balance_label.text = f"Balance: {gui_info.balance:_}".replace("_", " ")

        self._info = gui_info

    def _on_next(self, _):
        res = self._game_service.next_day(self._game_id)

        if res.success:
            self._error_label.text = ""

            # Doesn't look good, but okay for now
            if self._info.has_matches:
                App.get_running_app().switch_to_day_results()
        else:
            self._error_label.text = res.reason

        self.update()

    def _on_select_player(self, _):
        self._error_label.text = ""
        App.get_running_app().switch_to_player_selection()

    def _back_to_main_screen(self, _):
        self._game_service.save_game(self._game_id)

        App.get_running_app().switch_to_main(None)
