"""
Created December 22, 2025

@author montreal91
"""
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.layout import make_three_column_layout
from configuration.application_context import get_application_context
from core.ports.inbound.commands.select_club import SelectClubCommand
from core.queries.club_selection_screen_query import ClubSelectionScreenQuery

_INFO_LABEL_WIDTH = 360


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

        self._start_button = Button(
            text="Start New Story",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        self._start_button.disabled = True
        self._start_button.bind(on_press=self._start_new_story)
        self._layout.left_col.add_widget(self._start_button)

        back_button = Button(
            text="Back to Main Menu",
            font_size=30,
            size_hint=(None, None),
            size=button_size
        )
        back_button.bind(on_press=_back_to_main_screen)
        self._layout.left_col.add_widget(back_button)
        self._layout.left_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        self._layout.center_col.clear_widgets()
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
                size=button_size
            )
            button.bind(on_press=self._on_select)
            button.club_id = club.club_id
            self._layout.center_col.add_widget(button)
            self._club_buttons.append(button)

        self._layout.center_col.add_widget(Widget())
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
            ))
            self._layout.right_col.add_widget(Widget())
            return

        self._layout.right_col.add_widget(_make_info_title(club.club_name))
        self._layout.right_col.add_widget(_make_wrapped_label(
            text=f"{club.city}, {club.country}",
            font_size=22,
        ))

        if club.motto:
            self._layout.right_col.add_widget(_make_wrapped_label(
                text=f"[i]{club.motto}[/i]",
                font_size=24,
                markup=True,
            ))

        if club.description:
            self._layout.right_col.add_widget(_make_wrapped_label(
                text=club.description,
                font_size=22,
            ))

        self._layout.right_col.add_widget(Widget())


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)


def _make_info_title(text):
    return _make_wrapped_label(
        text=f"[b]{text}[/b]",
        font_size=30,
        markup=True,
    )


def _make_wrapped_label(text, font_size, markup=False):
    label = Label(
        text=text,
        font_size=font_size,
        markup=markup,
        size_hint=(None, None),
        width=dp(_INFO_LABEL_WIDTH),
        halign="left",
        valign="top",
    )
    label.text_size = (dp(_INFO_LABEL_WIDTH), None)
    label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
    return label
