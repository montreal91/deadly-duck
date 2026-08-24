"""
Created December 23, 2025

@author montreal91
"""
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.factories import make_label
from client.widgets.layout import make_three_column_layout
from client.widgets.opponent_player_details import PlayerDetailsWidget
from client.widgets.player_selection_table import PlayerSelectionTable
from core.ports.inbound.commands.select_player_for_match import SelectPlayerForMatchCommand

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 42
_ACTION_FONT_SIZE = 22
_RIGHT_TITLE_HEIGHT = 46
_RIGHT_LABEL_HEIGHT = 24
_RIGHT_TITLE_FONT_SIZE = 30
_RIGHT_LABEL_FONT_SIZE = 20
_COLUMN_HORIZONTAL_PADDING = 24
_MIN_COLUMN_CONTENT_WIDTH = 120


class PlayerSelectionScreen(Screen):
    def __init__(
            self,
            game_service,
            select_player_for_match_command_handler,
            **kwargs,
    ):
        super(PlayerSelectionScreen, self).__init__(**kwargs)
        self._game_service = game_service
        self._select_player_for_match_command_handler = select_player_for_match_command_handler

        self._layout = make_three_column_layout(
            title_text="Select Player",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3
        )
        self._layout.left_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.left_col.spacing = dp(6)
        self._layout.center_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.center_col.spacing = dp(6)
        self._layout.right_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.right_col.spacing = dp(6)

        back_button = _make_column_button("Back", self._layout.left_col)
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)

        self._opp_club_label = _make_column_label(
            text="Placeholder",
            column=self._layout.right_col,
            font_size=_RIGHT_TITLE_FONT_SIZE,
            height=_RIGHT_TITLE_HEIGHT,
        )
        self._layout.right_col.add_widget(self._opp_club_label)

        self._home_away_label = _make_column_label(
            text="Placeholder",
            column=self._layout.right_col,
            font_size=_RIGHT_LABEL_FONT_SIZE,
            height=_RIGHT_LABEL_HEIGHT,
        )
        self._layout.right_col.add_widget(self._home_away_label)

        self._opp_player_widget = PlayerDetailsWidget()
        self._layout.right_col.add_widget(self._opp_player_widget.widget)

        self._selection_table = PlayerSelectionTable()
        self._empty_label = _make_column_label(
            text="No match today.",
            column=self._layout.center_col,
            font_size=24,
            height=32,
        )

        self._submit_button = _make_column_button("Submit", self._layout.center_col)
        self._submit_button.bind(on_press=self._on_submit)

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
        self._layout.center_col.clear_widgets()

        if info.opponent is None:
            self._selection_table.update([])
            self._layout.center_col.add_widget(self._empty_label)
            self._layout.center_col.add_widget(Widget())
            self._layout.right_col.add_widget(_make_column_label(
                text="No opponent today.",
                column=self._layout.right_col,
                font_size=24,
                height=32,
            ))
            self._layout.right_col.add_widget(Widget())
            return

        self._opp_club_label.text = f"vs. {info.opponent.club_name}"
        self._layout.right_col.add_widget(self._opp_club_label)
        self._layout.right_col.add_widget(self._home_away_label)

        self._selection_table.update(info.players)
        self._layout.center_col.add_widget(self._selection_table.widget)
        self._layout.center_col.add_widget(self._submit_button)

        if info.opponent.player is not None:
            self._home_away_label.text = "Home"

            self._opp_player_widget.update(info.opponent.player)
            self._layout.right_col.add_widget(self._opp_player_widget.widget)
        else:
            self._home_away_label.text = "Away"

        self._layout.right_col.add_widget(Widget())
        self._layout.center_col.add_widget(Widget())

    def _on_submit(self, _):
        command = SelectPlayerForMatchCommand(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
            player_id=self._selection_table.selected_player_id,
        )
        self._select_player_for_match_command_handler(command)
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


def _make_column_label(text, column, font_size, height):
    label = Label(
        text=text,
        font_size=font_size,
        size_hint=(None, None),
        height=dp(height),
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
