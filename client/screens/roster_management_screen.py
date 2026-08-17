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
from client.widgets.roster_management_table import RosterManagementTable
from core.ports.inbound.commands.fire_player import FirePlayerCommand
from core.ports.inbound.commands.hire_new_player import HireNewPlayerCommand
from core.ports.inbound.commands.sign_player import SignPlayerCommand
from core.queries.roster_management_screen_query import RosterManagementScreenQuery


class RosterManagementScreen(Screen):
    def __init__(
            self,
            query_handler,
            hire_new_player_command_handler,
            sign_player_command_handler,
            fire_player_command_handler,
            **kwargs
    ):
        super(RosterManagementScreen, self).__init__(**kwargs)
        self._query_handler = query_handler
        self._hire_new_player_command_handler = hire_new_player_command_handler
        self._sign_player_command_handler = sign_player_command_handler
        self._fire_player_command_handler = fire_player_command_handler
        self._info = None

        self._layout = make_three_column_layout(
            title_text="Roster Management",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3
        )

        self._balance_label = make_label(text="Balance: 0", font_size=30)
        self._layout.left_col.add_widget(self._balance_label)

        hire_new_player_button = Button(
            text="Hire A New Player",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        hire_new_player_button.bind(on_press=self._on_hire_new_player)
        self._layout.left_col.add_widget(hire_new_player_button)

        self._layout.left_col.add_widget(Widget(size_hint_y=None, height=20))

        back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)

        self._roster_table = RosterManagementTable(
            on_sign_player=self._on_sign_player,
            on_fire_player=self._on_fire_player,
        )
        self._layout.center_col.add_widget(self._roster_table.widget)

        self._layout.left_col.add_widget(Widget())
        self._layout.center_col.add_widget(Widget())
        self._layout.right_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        query = RosterManagementScreenQuery(
            game_id=GameContext.get_instance().game_name,
            manager_club_id=GameContext.get_instance().club_id,
        )
        self._info = self._query_handler(query)
        self._balance_label.text = f"Balance: {self._info.balance:_}".replace("_", " ")
        self._roster_table.update(self._info.roster)

    def _on_hire_new_player(self, _):
        command = HireNewPlayerCommand(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
        )
        result = self._hire_new_player_command_handler(command)
        print(f"Hire new player command result: {result}")
        self.update()

    def _on_sign_player(self, player_id):
        command = SignPlayerCommand(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
            player_id=player_id,
        )
        result = self._sign_player_command_handler(command)
        print(f"Sign player command result: {result}")
        self.update()

    def _on_fire_player(self, player_id):
        command = FirePlayerCommand(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
            player_id=player_id,
        )
        result = self._fire_player_command_handler(command)
        print(f"Fire player command result: {result}")
        self.update()


def _on_back(_):
    App.get_running_app().return_to_game()
