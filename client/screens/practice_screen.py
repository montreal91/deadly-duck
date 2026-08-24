"""
Created August 17, 2026

@author montreal91
"""
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.layout import make_two_column_layout
from client.widgets.practice_table import PracticeTable
from core.ports.inbound.commands.select_coach_for_player import SelectCoachForPlayerCommand
from core.queries.practice_screen_query import PracticeScreenQuery

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 42
_ACTION_FONT_SIZE = 22
_INFO_HEIGHT = 28
_INFO_FONT_SIZE = 22
_COLUMN_HORIZONTAL_PADDING = 24
_MIN_COLUMN_CONTENT_WIDTH = 120


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

        self._layout = make_two_column_layout(
            title_text="Practice",
            left_width_hint=0.22,
            center_width_hint=0.78,
        )
        self._layout.left_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.left_col.spacing = dp(6)
        self._layout.center_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.center_col.spacing = dp(6)

        self._balance_label = _make_column_label("Balance: 0", self._layout.left_col)
        self._layout.left_col.add_widget(self._balance_label)

        back_button = _make_column_button("Back", self._layout.left_col)
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)

        self._practice_table = PracticeTable(
            on_select_coach=self._on_select_coach,
        )
        self._layout.center_col.add_widget(self._practice_table.widget)

        self._layout.left_col.add_widget(Widget())
        self._layout.center_col.add_widget(Widget())

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


def _make_column_button(text, column):
    button = Button(
        text=text,
        font_size=_ACTION_FONT_SIZE,
        size_hint=(None, None),
        height=dp(_ACTION_HEIGHT),
    )
    _bind_width_to_column(button, column, _ACTION_WIDTH)
    return button


def _make_column_label(text, column):
    label = Label(
        text=text,
        font_size=_INFO_FONT_SIZE,
        size_hint=(None, None),
        height=dp(_INFO_HEIGHT),
        halign="left",
        valign="middle",
    )
    _bind_width_to_column(label, column, _ACTION_WIDTH, wrap_text=True)
    return label


def _bind_width_to_column(widget, column, max_width, wrap_text=False):
    def sync_width(_, width):
        widget.width = min(_column_content_width(width), dp(max_width))
        if wrap_text:
            widget.text_size = (widget.width, None)

    column.bind(width=sync_width)
    sync_width(column, column.width)


def _column_content_width(column_width):
    return max(
        column_width - dp(_COLUMN_HORIZONTAL_PADDING),
        dp(_MIN_COLUMN_CONTENT_WIDTH),
    )
