"""
Created December 21, 2025

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
from client.widgets.playoffs_bracket_widget import PlayoffsBracketWidget
from client.widgets.standings_table_widget import StandingsTableWidget
from client.widgets.upcoming_days_widget import UpcomingDaysWidget
from client.widgets.upcoming_match_widget import UpcomingMatchWidget
from core.competition import CompetitionType
from core.ports.inbound.commands.next_day import NextDayCommand

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 42
_INFO_HEIGHT = 28
_ERROR_HEIGHT = 36
_ACTION_FONT_SIZE = 22
_INFO_FONT_SIZE = 22
_ERROR_FONT_SIZE = 18
_MIN_COLUMN_CONTENT_WIDTH = 120
_LEFT_COLUMN_HORIZONTAL_PADDING = 24


class GameScreen(Screen):
    def __init__(
            self,
            game_service,
            next_day_command_handler,
            query_handler,
            **kwargs
    ):
        super(GameScreen, self).__init__(**kwargs)

        self._info = None
        self._game_service = game_service
        self._next_day_command_handler = next_day_command_handler
        self._query_handler = query_handler

        self._game_id = None
        self._club_id = None

        self._layout = make_three_column_layout(
            title_text="",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3,
        )
        self._layout.left_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.left_col.spacing = dp(6)
        self._layout.right_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.right_col.spacing = dp(4)

        self._upcoming_match_widget = UpcomingMatchWidget()
        self._layout.right_col.add_widget(self._upcoming_match_widget.root)
        self._layout.right_col.add_widget(Widget(size_hint_y=None, height=dp(8)))
        self._upcoming_days_widget = UpcomingDaysWidget()
        self._layout.right_col.add_widget(self._upcoming_days_widget.root)

        self._date_label = _make_left_label("PlaceHolder", self._layout.left_col)
        self._layout.left_col.add_widget(self._date_label)

        self._season_label = _make_left_label("PlaceHolder", self._layout.left_col)
        self._layout.left_col.add_widget(self._season_label)

        self._current_stage_label = _make_left_label("PlaceHolder", self._layout.left_col)
        self._layout.left_col.add_widget(self._current_stage_label)

        self._balance_label = _make_left_label("PlaceHolder", self._layout.left_col)
        self._layout.left_col.add_widget(self._balance_label)

        self._error_label = _make_left_label(
            " ",
            self._layout.left_col,
            font_size=_ERROR_FONT_SIZE,
        )
        self._error_label.color = (0.8, 0.2, 0.2, 1)
        self._layout.left_col.add_widget(self._error_label)

        self._next_button = _make_left_button("Next", self._layout.left_col)
        self._next_button.bind(on_press=self._on_next)
        self._layout.left_col.add_widget(self._next_button)

        self._select_player_button = _make_left_button("Select Player", self._layout.left_col)
        self._select_player_button.bind(on_press=self._on_select_player)
        self._layout.left_col.add_widget(self._select_player_button)

        self._level_up_button = _make_left_button("Level Up", self._layout.left_col)
        self._level_up_button.disabled = True
        self._level_up_button.bind(on_press=self._on_level_up)
        self._layout.left_col.add_widget(self._level_up_button)

        self._practice_button = _make_left_button("Practice", self._layout.left_col)
        self._practice_button.bind(on_press=self._on_practice)
        self._layout.left_col.add_widget(self._practice_button)

        self._roster_management_button = _make_left_button(
            "Roster Management",
            self._layout.left_col,
        )
        self._roster_management_button.bind(on_press=self._on_roster_management)
        self._layout.left_col.add_widget(self._roster_management_button)

        self._res_button = _make_left_button("Results", self._layout.left_col)
        self._res_button.bind(on_press=_on_results)
        self._layout.left_col.add_widget(self._res_button)

        self._back_button = _make_left_button("Back", self._layout.left_col)
        self._back_button.bind(on_press=self._back_to_main_screen)
        self._layout.left_col.add_widget(self._back_button)

        self._standings_table = StandingsTableWidget()
        self._playoffs_bracket = PlayoffsBracketWidget()

        self._layout.left_col.add_widget(Widget())
        self._layout.right_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def init_game_data(self):
        self._game_id = GameContext.get_instance().game_name
        self._club_id = GameContext.get_instance().club_id

    def update(self):
        info = self._game_service.get_main_screen_info(self._game_id, self._club_id)
        gui_info = self._query_handler(self._game_id, self._club_id)

        self._layout.title.text = info.club_name
        self._date_label.text = f"Date: {gui_info.day}"
        self._season_label.text = f"Your Season: {gui_info.season}"
        self._current_stage_label.text = f"Current Stage: {gui_info.current_competition}"
        self._balance_label.text = f"Balance: {gui_info.balance:_}".replace("_", " ")
        self._level_up_button.text = f"Level Up [{gui_info.level_ups_count}]"
        self._level_up_button.disabled = gui_info.level_ups_count <= 0

        self._info = gui_info

        self._upcoming_match_widget.update(gui_info.upcoming_match)
        self._upcoming_days_widget.update(gui_info.upcoming_days)
        self._update_center_widget(gui_info)

    def _on_next(self, _):
        res = self._next_day_command_handler(NextDayCommand(self._game_id))

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

    def _on_level_up(self, _):
        self._error_label.text = ""
        App.get_running_app().switch_to_level_up()

    @staticmethod
    def _on_practice(_):
        App.get_running_app().switch_to_practice()

    @staticmethod
    def _on_roster_management(_):
        App.get_running_app().switch_to_roster_management()


    @staticmethod
    def _back_to_main_screen(_):
        App.get_running_app().switch_to_main(None)

    def _update_center_widget(self, gui_info):
        self._layout.center_col.clear_widgets()

        if gui_info.competition_type == CompetitionType.CHAMPIONSHIP:
            self._standings_table.update(gui_info.standings)
            self._layout.center_col.add_widget(self._standings_table.widget)
        elif gui_info.competition_type == CompetitionType.PLAY_OFFS:
            self._playoffs_bracket.update(gui_info.standings)
            self._layout.center_col.add_widget(self._playoffs_bracket.widget)
        else:
            raise Exception("Unknown competition type.")


def _on_results(_):
    App.get_running_app().switch_to_day_results()


def _make_left_button(text, column):
    button = Button(
        text=text,
        font_size=_ACTION_FONT_SIZE,
        size_hint=(None, None),
        height=dp(_ACTION_HEIGHT),
    )
    _bind_width_to_column(button, column, _ACTION_WIDTH)
    return button


def _make_left_label(text, column, font_size=_INFO_FONT_SIZE):
    label = Label(
        text=text,
        font_size=font_size,
        size_hint=(None, None),
        height=dp(_ERROR_HEIGHT if font_size == _ERROR_FONT_SIZE else _INFO_HEIGHT),
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
        column_width - dp(_LEFT_COLUMN_HORIZONTAL_PADDING),
        dp(_MIN_COLUMN_CONTENT_WIDTH),
    )
