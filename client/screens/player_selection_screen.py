"""
Created December 23, 2025

@author montreal91
"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.factories import make_label
from client.widgets.layout import make_three_column_layout
from client.widgets.opponent_player_details import PlayerDetailsWidget
from client.widgets.player_selection_table import PlayerSelectionTable
from configuration.application_context import get_application_context


class PlayerSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super(PlayerSelectionScreen, self).__init__(**kwargs)
        self._game_service = get_application_context().game_service

        self._layout = make_three_column_layout(
            title_text="Select Player",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3
        )

        back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)

        self._opp_club_label = make_label(text="Placeholder", font_size=40)
        self._layout.right_col.add_widget(self._opp_club_label)

        self._home_away_label = make_label(text="Placeholder", font_size=20)
        self._layout.right_col.add_widget(self._home_away_label)

        self._opp_player_widget = PlayerDetailsWidget()
        self._layout.right_col.add_widget(self._opp_player_widget.widget)

        self._layout.center_col.add_widget(make_label(""))
        self._selection_table = PlayerSelectionTable()
        self._layout.center_col.add_widget(self._selection_table.widget)

        submit_button = Button(
            text="Submit",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        submit_button.bind(on_press=self._on_submit)
        self._layout.center_col.add_widget(submit_button)

        self._layout.left_col.add_widget(Widget())
        self._layout.right_col.add_widget(Widget())
        self._layout.center_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        info = self._game_service.get_player_selection_gui_info(
            GameContext.get_instance().game_name,
            GameContext.get_instance().club_id,
        )

        self._layout.right_col.clear_widgets()

        if info.opponent is None:
            return

        self._opp_club_label.text = f"vs. {info.opponent.club_name}"
        self._layout.right_col.add_widget(self._opp_club_label)
        self._layout.right_col.add_widget(self._home_away_label)

        self._selection_table.update(info.players)

        if info.opponent.player is not None:
            self._home_away_label.text = "Home"

            self._opp_player_widget.update(info.opponent.player)
            self._layout.right_col.add_widget(self._opp_player_widget.widget)
        else:
            self._home_away_label.text = "Away"

        self._layout.right_col.add_widget(Widget())

    def _on_submit(self, _):
        self._game_service.set_player(
            game_id=GameContext.get_instance().game_name,
            manager_club_id=GameContext.get_instance().club_id,
            player_id=self._selection_table.selected_player_id,
        )
        self.update()


def _on_back(_):
    App.get_running_app().return_to_game()
