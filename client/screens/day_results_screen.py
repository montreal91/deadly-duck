"""
Created December 24, 2025

@author montreal91
"""
from kivy.app import App
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.layout import make_three_column_layout
from core.queries.day_results_query import DayResultsQuery

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 42
_ACTION_FONT_SIZE = 22
_COLUMN_HORIZONTAL_PADDING = 24
_MIN_COLUMN_CONTENT_WIDTH = 120
_RESULT_HEIGHT = 84
_USER_RESULT_HEIGHT = 108


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
        self._layout.left_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.left_col.spacing = dp(6)
        self._layout.center_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.center_col.spacing = dp(6)

        to_game_button = _make_column_button("To Game", self._layout.left_col)
        to_game_button.bind(on_press=_on_to_game)
        self._layout.left_col.add_widget(to_game_button)

        self._result_list = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(1, None),
        )
        self._result_list.bind(minimum_height=self._result_list.setter("height"))

        result_scroll = ScrollView(
            do_scroll_x=False,
            size_hint=(1, 1),
        )
        result_scroll.add_widget(self._result_list)
        self._layout.center_col.add_widget(result_scroll)

        self._layout.left_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        q_res = self._day_results_query_handler(DayResultsQuery(
            game_id=GameContext.get_instance().game_name,
            manager_club_id=GameContext.get_instance().club_id,
        ))

        self._result_list.clear_widgets()

        cid = GameContext.get_instance().club_id
        match_results = _sort_manager_club_results_first(
            q_res.match_results_list,
            cid,
        )

        for res in match_results:
            is_user_result = res.experience_gained is not None
            line = BoxLayout(
                orientation="vertical",
                size_hint=(None, None),
                height=dp(_USER_RESULT_HEIGHT if is_user_result else _RESULT_HEIGHT),
            )
            _bind_width_to_column(line, self._layout.center_col, 9999)

            if is_user_result:
                with line.canvas.before:
                    line._bg_color = Color(rgba=(.2, .2, .2, 1))
                    line._bg_rect = Rectangle(pos=line.pos, size=line.size)
                line.bind(pos=_update_bg, size=_update_bg)

            line.add_widget(_make_result_label(
                text=f"{res.home_club_name} vs. {res.away_club_name}",
                font_size=26,
                height=30,
                width_source=self._layout.center_col,
            ))
            line.add_widget(_make_result_label(
                text=f"{res.home_player_name} vs. {res.away_player_name}",
                font_size=22,
                height=26,
                width_source=self._layout.center_col,
            ))
            line.add_widget(_make_result_label(
                text=res.score,
                font_size=22,
                height=26,
                width_source=self._layout.center_col,
            ))
            if is_user_result:
                line.add_widget(_make_result_label(
                    text=_make_experience_text(
                        res.user_player_name,
                        res.experience_gained,
                    ),
                    font_size=18,
                    height=24,
                    width_source=self._layout.center_col,
                ))
            self._result_list.add_widget(line)


def _on_to_game(_):
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


def _make_result_label(text, font_size, height, width_source):
    label = Label(
        text=text,
        font_size=font_size,
        size_hint=(None, None),
        height=dp(height),
        halign="left",
        valign="middle",
    )
    _bind_width_to_column(label, width_source, 9999, wrap_text=True)
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


def _sort_manager_club_results_first(results, manager_club_id):
    return sorted(
        results,
        key=lambda result: int(
            manager_club_id not in (result.home_club_id, result.away_club_id)
        ),
    )


def _make_experience_text(player_name, experience_gained):
    return f"{player_name} gained {experience_gained} pts. of experience."


def _update_bg(self, *_):
    self._bg_rect.pos = self.pos
    self._bg_rect.size = self.size
