"""
Created December 24, 2025

@author montreal91
"""
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.factories import make_label
from client.widgets.layout import make_three_column_layout
from core.queries.day_results_query import DayResultsQuery


class DayResultsScreen(Screen):
    def __init__(self, day_results_query_handler, **kwargs):
        super(DayResultsScreen, self).__init__(**kwargs)

        self._day_results_query_handler = day_results_query_handler

        self._layout = make_three_column_layout(
            title_text="Results",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3,
        )

        to_game_button = Button(
            text="To Game",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        to_game_button.bind(on_press=_on_to_game)
        self._layout.left_col.add_widget(to_game_button)

        self._layout.left_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        q_res = self._day_results_query_handler(DayResultsQuery(
            game_id=GameContext.get_instance().game_name,
            manager_club_id=GameContext.get_instance().club_id,
        ))

        self._layout.center_col.clear_widgets()

        for res in q_res.match_results_list:
            line = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(80))
            cid = GameContext.get_instance().club_id

            if res.home_club_id == cid or res.away_club_id == cid:
                with line.canvas.before:
                    line._bg_color = Color(rgba=(.2, .2, .2, 1))
                    line._bg_rect = Rectangle(pos=line.pos, size=line.size)
                line.bind(size=_update_bg)

            line.add_widget(make_label(
                text=f"{res.home_club_name} vs. {res.away_club_name}",
                font_size=35,
            ))
            line.add_widget(make_label(
                text=f"{res.home_player_name} vs. {res.away_player_name}",
                font_size=30,
            ))
            line.add_widget(make_label(
                text=res.score,
                font_size=30,
            ))
            self._layout.center_col.add_widget(line)

        self._layout.center_col.add_widget(Widget())


def _on_to_game(_):
    App.get_running_app().return_to_game()


def _update_bg(self, *_):
    self._bg_rect.pos = self.pos
    self._bg_rect.size = self.size
