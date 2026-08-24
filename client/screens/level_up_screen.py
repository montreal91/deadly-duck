"""
Created August 20, 2026

@author montreal91
"""
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from client.game_context import GameContext
from client.widgets.factories import make_label
from client.widgets.layout import make_three_column_layout
from configuration.config_game import GameplayConstants
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommand,
)
from core.queries.level_up_screen_query import LevelUpScreenQuery

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 42
_ACTION_FONT_SIZE = 22
_PLAYER_BUTTON_HEIGHT = 42
_PLAYER_BUTTON_FONT_SIZE = 20
_STAT_LABEL_WIDTH_HINT = 0.42
_STAT_VALUE_WIDTH_HINT = 0.30
_STAT_CONTROL_WIDTH_HINT = 0.14
_STAT_CONTROL_SPACING = 4
_COLUMN_HORIZONTAL_PADDING = 24
_MIN_COLUMN_CONTENT_WIDTH = 120
_SKILL_TECHNIQUE = "technique"
_SKILL_ENDURANCE = "endurance"


class LevelUpScreen(Screen):
    def __init__(
            self,
            query_handler,
            improve_player_skill_command_handler,
            **kwargs,
    ):
        super(LevelUpScreen, self).__init__(**kwargs)
        self._query_handler = query_handler
        self._improve_player_skill_command_handler = (
            improve_player_skill_command_handler
        )
        self._players = []
        self._selected_player = None
        self._skill_points_by_player_id = {}
        self._message = ""

        self._layout = make_three_column_layout(
            title_text="Level Up",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3,
        )
        self._layout.left_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.left_col.spacing = dp(6)
        self._layout.center_col.padding = [dp(12), 0, dp(12), dp(8)]
        self._layout.center_col.spacing = dp(6)

        back_button = _make_column_button("Back", self._layout.left_col)
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)
        self._layout.left_col.add_widget(Widget())

        self._player_list_col = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(0.40, 1),
        )
        self._player_stats_col = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint=(0.60, 1),
        )
        content = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint=(1, 1),
        )
        content.add_widget(self._player_list_col)
        content.add_widget(self._player_stats_col)
        self._layout.center_col.add_widget(content)

        self._layout.right_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update(self):
        query_result = self._query_handler(LevelUpScreenQuery(
            game_id=GameContext.get_instance().game_name,
            club_id=GameContext.get_instance().club_id,
        ))
        self._players = query_result.players
        self._skill_points_by_player_id = {
            player.player_id: self._skill_points_by_player_id.get(
                player.player_id,
                _empty_skill_points(),
            )
            for player in self._players
        }
        self._selected_player = self._players[0] if self._players else None
        self._message = ""
        self._render()

    def _render(self):
        self._render_player_list()
        self._render_player_stats()

    def _render_player_list(self):
        self._player_list_col.clear_widgets()

        if not self._players:
            self._player_list_col.add_widget(make_label(
                text="No players to level up.",
                font_size=22,
            ))
            self._player_list_col.add_widget(Widget())
            return

        for player in self._players:
            button = Button(
                text=player.full_name,
                font_size=_PLAYER_BUTTON_FONT_SIZE,
                size_hint=(1, None),
                height=dp(_PLAYER_BUTTON_HEIGHT),
                background_color=_button_color(
                    player == self._selected_player,
                ),
            )
            button.bind(
                on_press=lambda _, selected=player: (
                    self._on_player_selected(selected)
                ),
            )
            self._player_list_col.add_widget(button)

        self._player_list_col.add_widget(Widget())

    def _render_player_stats(self):
        self._player_stats_col.clear_widgets()

        if self._selected_player is None:
            self._player_stats_col.add_widget(Widget())
            return

        player = self._selected_player
        skill_points = self._get_selected_skill_points()
        allocated_points = sum(skill_points.values())
        remaining_points = player.available_skill_points - allocated_points

        self._player_stats_col.add_widget(_make_name_label(player.full_name))

        rows = (
            ("Level", player.level),
            (
                "Skill Points",
                remaining_points,
            ),
        )

        for title, value in rows:
            self._player_stats_col.add_widget(_make_stat_row(title, value))

        self._player_stats_col.add_widget(_make_skill_row(
            title="Technique",
            value=player.technique,
            skill_delta=_skill_delta(skill_points[_SKILL_TECHNIQUE]),
            can_add=remaining_points > 0,
            can_remove=skill_points[_SKILL_TECHNIQUE] > 0,
            on_add=lambda _: self._add_skill_point(_SKILL_TECHNIQUE),
            on_remove=lambda _: self._remove_skill_point(_SKILL_TECHNIQUE),
        ))
        self._player_stats_col.add_widget(_make_skill_row(
            title="Endurance",
            value=player.endurance,
            skill_delta=_skill_delta(skill_points[_SKILL_ENDURANCE]),
            can_add=remaining_points > 0,
            can_remove=skill_points[_SKILL_ENDURANCE] > 0,
            on_add=lambda _: self._add_skill_point(_SKILL_ENDURANCE),
            on_remove=lambda _: self._remove_skill_point(_SKILL_ENDURANCE),
        ))

        submit_button = Button(
            text="Submit",
            font_size=_ACTION_FONT_SIZE,
            size_hint=(1, None),
            height=dp(_ACTION_HEIGHT),
            disabled=allocated_points == 0,
        )
        submit_button.bind(on_press=self._on_submit)
        self._player_stats_col.add_widget(submit_button)

        if self._message:
            self._player_stats_col.add_widget(make_label(
                text=self._message,
                font_size=18,
            ))

        self._player_stats_col.add_widget(Widget())

    def _on_player_selected(self, player):
        self._selected_player = player
        self._message = ""
        self._render()

    def _add_skill_point(self, skill):
        skill_points = self._get_selected_skill_points()
        player = self._selected_player
        if player is None:
            return

        if sum(skill_points.values()) >= player.available_skill_points:
            return

        skill_points[skill] += 1
        self._render_player_stats()

    def _remove_skill_point(self, skill):
        skill_points = self._get_selected_skill_points()

        if skill_points[skill] <= 0:
            return

        skill_points[skill] -= 1
        self._render_player_stats()

    def _get_selected_skill_points(self):
        return self._skill_points_by_player_id[
            self._selected_player.player_id
        ]

    def _on_submit(self, _):
        player = self._selected_player
        skill_points = self._get_selected_skill_points()

        result = self._improve_player_skill_command_handler(
            ImprovePlayerSkillCommand(
                game_id=GameContext.get_instance().game_name,
                club_id=GameContext.get_instance().club_id,
                player_id=player.player_id,
                skill_points=dict(skill_points),
            ),
        )

        if result.success:
            self._apply_successful_skill_improvement(player, skill_points)
            self._skill_points_by_player_id[player.player_id] = (
                _empty_skill_points()
            )
            self._message = ""
            self._render()
            return

        self._message = result.message
        self._render_player_stats()

    def _apply_successful_skill_improvement(self, player, skill_points):
        updated_player = player._replace(
            technique=(
                player.technique
                + _skill_delta(skill_points[_SKILL_TECHNIQUE])
            ),
            endurance=(
                player.endurance
                + _skill_delta(skill_points[_SKILL_ENDURANCE])
            ),
            available_skill_points=(
                player.available_skill_points
                - sum(skill_points.values())
            ),
        )

        self._players = [
            updated_player if item.player_id == player.player_id else item
            for item in self._players
        ]
        self._selected_player = updated_player


def _on_back(_):
    App.get_running_app().return_to_game()


def _button_color(is_selected):
    if is_selected:
        return 0.35, 0.55, 0.80, 1
    return 1, 1, 1, 1


def _make_name_label(name):
    label = Label(
        text=f"[b]{name}[/b]",
        font_size=24,
        markup=True,
        size_hint=(1, None),
        height=dp(34),
        halign="left",
        valign="middle",
    )
    label.markup = True
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label


def _make_stat_row(title, value):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(34),
    )
    row.add_widget(_make_stat_cell(
        value=title,
        width_hint=_STAT_LABEL_WIDTH_HINT,
        is_title=True,
    ))
    row.add_widget(_make_stat_cell(
        value=str(value),
        width_hint=_STAT_VALUE_WIDTH_HINT,
    ))
    return row


def _make_skill_row(
        title,
        value,
        skill_delta,
        can_add,
        can_remove,
        on_add,
        on_remove,
):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(38),
        spacing=dp(_STAT_CONTROL_SPACING),
    )
    row.add_widget(_make_stat_cell(
        value=title,
        width_hint=_STAT_LABEL_WIDTH_HINT,
        is_title=True,
    ))
    row.add_widget(_make_stat_cell(
        value=f"{value} (+{skill_delta})",
        width_hint=_STAT_VALUE_WIDTH_HINT,
    ))

    minus_button = Button(
        text="-",
        font_size=24,
        size_hint=(_STAT_CONTROL_WIDTH_HINT, None),
        height=dp(34),
        disabled=not can_remove,
    )
    minus_button.bind(on_press=on_remove)
    row.add_widget(minus_button)

    plus_button = Button(
        text="+",
        font_size=24,
        size_hint=(_STAT_CONTROL_WIDTH_HINT, None),
        height=dp(34),
        disabled=not can_add,
    )
    plus_button.bind(on_press=on_add)
    row.add_widget(plus_button)

    return row


def _make_stat_cell(value, width_hint, is_title=False):
    label = Label(
        text=f"[b]{value}[/b]" if is_title else value,
        font_size=20,
        markup=is_title,
        size_hint=(width_hint, None),
        height=dp(34),
        halign="left",
        valign="middle",
    )
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label


def _make_column_button(text, column):
    button = Button(
        text=text,
        font_size=_ACTION_FONT_SIZE,
        size_hint=(None, None),
        height=dp(_ACTION_HEIGHT),
    )
    _bind_width_to_column(button, column, _ACTION_WIDTH)
    return button


def _bind_width_to_column(widget, column, max_width):
    def sync_width(_, width):
        widget.width = min(_column_content_width(width), dp(max_width))

    column.bind(width=sync_width)
    sync_width(column, column.width)


def _column_content_width(column_width):
    return max(
        column_width - dp(_COLUMN_HORIZONTAL_PADDING),
        dp(_MIN_COLUMN_CONTENT_WIDTH),
    )


def _empty_skill_points():
    return {
        _SKILL_TECHNIQUE: 0,
        _SKILL_ENDURANCE: 0,
    }


def _skill_delta(skill_points):
    return skill_points * GameplayConstants.SKILL_GROWTH_PER_POINT.value
