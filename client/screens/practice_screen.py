"""
Created August 17, 2026

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
from client.widgets.practice_table import PracticeTable
from core.ports.inbound.commands.select_coach_for_player import SelectCoachForPlayerCommand
from core.queries.practice_screen_query import PracticeScreenQuery


class PracticeScreen(Screen):
    def __init__(
            self,
            query_handler,
            select_coach_for_player_command_handler,
            **kwargs
    ):
        super(PracticeScreen, self).__init__(**kwargs)
        self._query_handler = query_handler
        self._select_coach_for_player_command_handler = select_coach_for_player_command_handler
        self._info = None

        self._layout = make_three_column_layout(
            title_text="Practice",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3
        )

        self._balance_label = make_label(text="Balance: 0", font_size=30)
        self._layout.left_col.add_widget(self._balance_label)

        back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)

        self._practice_table = PracticeTable(
            on_select_coach=self._on_select_coach,
        )
        self._layout.center_col.add_widget(self._practice_table.widget)

        self._layout.left_col.add_widget(Widget())
        self._layout.center_col.add_widget(Widget())
        self._layout.right_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        query = PracticeScreenQuery(
            game_id=GameContext.get_instance().game_name,
            manager_club_id=GameContext.get_instance().club_id,
        )
        self._info = self._query_handler(query)
        self._balance_label.text = f"Balance: {self._info.balance:_}".replace("_", " ")
        self._practice_table.update(self._info.players)

    def _on_select_coach(self, player_id, coach_index):
        command = SelectCoachForPlayerCommand(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
            player_id=player_id,
            coach_index=coach_index,
        )
        self._select_coach_for_player_command_handler(command)
        self.update()


def _on_back(_):
    App.get_running_app().return_to_game()
