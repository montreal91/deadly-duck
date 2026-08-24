"""
Created December 22, 2025

@author montreal91
"""
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.layout import make_three_column_layout
from configuration.application_context import get_application_context
from core.ports.inbound.commands.select_club import SelectClubCommand
from core.queries.club_selection_screen_query import ClubSelectionScreenQuery

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 50
_INFO_LABEL_MAX_WIDTH = 520
_CLUB_BUTTON_MAX_WIDTH = 350


class ClubSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super(ClubSelectionScreen, self).__init__(**kwargs)
        self._current_id = None
        self._club_infos = {}
        self._game_service = get_application_context().game_service
        self._query_handler = get_application_context().select_club_screen_query_handler
        self._command_handler = get_application_context().select_club_command_handler

        self._layout = make_three_column_layout(
            title_text="Select Your Club",
            left_width_hint=0.25,
            center_width_hint=0.35,
            right_width_hint=0.4,
        )

        self._club_buttons = []
        self._club_list = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None),
        )
        self._club_list.bind(minimum_height=self._club_list.setter("height"))

        club_scroll = ScrollView(
            do_scroll_x=False,
            size_hint=(1, 1),
        )
        club_scroll.add_widget(self._club_list)
        self._layout.center_col.add_widget(club_scroll)

        self._start_button = Button(
            text="Start New Story",
            font_size=30,
            size_hint=(None, None),
            height=dp(_ACTION_HEIGHT),
        )
        self._bind_width_to_column(self._start_button, self._layout.left_col, _ACTION_WIDTH)
        self._start_button.disabled = True
        self._start_button.bind(on_press=self._start_new_story)
        self._layout.left_col.add_widget(self._start_button)

        back_button = Button(
            text="Back to Main Menu",
            font_size=30,
            size_hint=(None, None),
            height=dp(_ACTION_HEIGHT),
        )
        self._bind_width_to_column(back_button, self._layout.left_col, _ACTION_WIDTH)
        back_button.bind(on_press=_back_to_main_screen)
        self._layout.left_col.add_widget(back_button)
        self._layout.left_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        self._club_list.clear_widgets()
        self._club_buttons = []
        self._club_infos = {}
        self._current_id = None

        query = ClubSelectionScreenQuery(game_id=GameContext.get_instance().game_name)

        for club in self._query_handler(query).club_infos:
            self._club_infos[club.club_id] = club
            button = ToggleButton(
                text=club.club_name,
                group="clubs",
                size_hint=(None, None),
                height=dp(_ACTION_HEIGHT),
            )
            self._bind_width_to_column(
                button,
                self._layout.center_col,
                _CLUB_BUTTON_MAX_WIDTH,
            )
            button.bind(on_press=self._on_select)
            button.club_id = club.club_id
            self._club_list.add_widget(button)
            self._club_buttons.append(button)

        self._start_button.disabled = True
        self._render_club_info(None)

    def _on_select(self, btn):
        if btn.state == "down":
            self._current_id = btn.club_id
            self._start_button.disabled = False
            self._render_club_info(self._club_infos[btn.club_id])

    def _start_new_story(self, _):
        context = GameContext.get_instance()
        context.club_id = self._current_id

        command = SelectClubCommand(
            game_id=context.game_name,
            club_id=context.club_id,
        )

        self._command_handler(command)
        App.get_running_app().start_game()

    def _render_club_info(self, club):
        self._layout.right_col.clear_widgets()

        if club is None:
            self._layout.right_col.add_widget(_make_info_title(
                "Select a club",
                self._layout.right_col,
            ))
            self._layout.right_col.add_widget(Widget())
            return

        self._layout.right_col.add_widget(_make_info_title(
            club.club_name,
            self._layout.right_col,
        ))
        self._layout.right_col.add_widget(_make_wrapped_label(
            text=f"{club.city}, {club.country}",
            font_size=22,
            width_source=self._layout.right_col,
        ))

        if club.motto:
            self._layout.right_col.add_widget(_make_wrapped_label(
                text=f"[i]{club.motto}[/i]",
                font_size=24,
                markup=True,
                width_source=self._layout.right_col,
            ))

        if club.description:
            self._layout.right_col.add_widget(_make_wrapped_label(
                text=club.description,
                font_size=22,
                width_source=self._layout.right_col,
            ))

        self._layout.right_col.add_widget(Widget())

    @staticmethod
    def _bind_width_to_column(widget, column, max_width):
        def sync_width(_, width):
            widget.width = min(_column_content_width(width), dp(max_width))

        column.bind(width=sync_width)
        sync_width(column, column.width)


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)


def _make_info_title(text, width_source):
    return _make_wrapped_label(
        text=f"[b]{text}[/b]",
        font_size=30,
        markup=True,
        width_source=width_source,
    )


def _make_wrapped_label(text, font_size, markup=False, width_source=None):
    label = Label(
        text=text,
        font_size=font_size,
        markup=markup,
        size_hint=(None, None),
        halign="left",
        valign="top",
    )
    label.bind(
        texture_size=lambda inst, val: setattr(inst, "height", val[1]),
    )
    if width_source is not None:
        def sync_width(_, width):
            label.width = min(
                _column_content_width(width),
                dp(_INFO_LABEL_MAX_WIDTH),
            )
            label.text_size = (label.width, None)

        width_source.bind(width=sync_width)
        sync_width(width_source, width_source.width)

    return label


def _column_content_width(column_width):
    return max(column_width - dp(60), dp(120))
