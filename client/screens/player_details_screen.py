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

from client.constants import button_size
from client.game_context import GameContext
from client.widgets.factories import make_label
from client.widgets.layout import make_three_column_layout
from core.queries.player_details_screen_query import PlayerDetailsScreenQuery

_STAT_LABEL_WIDTH = 160
_STAT_SPACER_WIDTH = 10
_STAT_VALUE_WIDTH = 260


class PlayerDetailsScreen(Screen):
    def __init__(self, query_handler, **kwargs):
        super(PlayerDetailsScreen, self).__init__(**kwargs)
        self._query_handler = query_handler
        self._player_id = None

        self._layout = make_three_column_layout(
            title_text="Player Details",
            left_width_hint=0.2,
            center_width_hint=0.5,
            right_width_hint=0.3,
        )

        back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            size=button_size,
        )
        back_button.bind(on_press=_on_back)
        self._layout.left_col.add_widget(back_button)
        self._layout.left_col.add_widget(Widget())
        self._layout.right_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def open_player(self, player_id):
        self._player_id = player_id
        self.update()

    def update(self):
        self._layout.center_col.clear_widgets()

        if self._player_id is None:
            self._layout.center_col.add_widget(make_label(
                text="No player selected.",
                font_size=30,
            ))
            self._layout.center_col.add_widget(Widget())
            return

        query_result = self._query_handler(PlayerDetailsScreenQuery(
            game_id=GameContext.get_instance().game_name,
            player_id=self._player_id,
        ))

        if not query_result.success:
            self._layout.center_col.add_widget(make_label(
                text=query_result.message,
                font_size=30,
            ))
            self._layout.center_col.add_widget(Widget())
            return

        player = query_result.player
        name_label = make_label(
            text=f"[b]{player.name}[/b]",
            font_size=36,
        )
        name_label.markup = True
        self._layout.center_col.add_widget(name_label)

        rows = (
            ("Club", player.club_name),
            ("Age", player.age),
            ("Level", player.level),
            (
                "Experience",
                f"{player.experience}/{player.next_level_experience}",
            ),
            ("Technique", player.technique),
            ("Endurance", player.endurance),
            (
                "Stamina",
                f"{player.current_stamina}/{player.max_stamina}",
            ),
            ("Exhaustion", player.exhaustion),
            ("Contract", player.contract_status),
        )

        for title, value in rows:
            self._layout.center_col.add_widget(_make_stat_row(title, value))

        self._layout.center_col.add_widget(Widget())


def _on_back(_):
    App.get_running_app().switch_to_roster_management()


def _make_stat_row(title, value):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(34),
    )
    row.add_widget(_make_stat_cell(
        value=title,
        width=_STAT_LABEL_WIDTH,
        is_title=True,
    ))
    row.add_widget(Widget(size_hint_x=None, width=dp(_STAT_SPACER_WIDTH)))
    row.add_widget(_make_stat_cell(
        value=str(value),
        width=_STAT_VALUE_WIDTH,
    ))
    return row


def _make_stat_cell(value, width, is_title=False):
    label = Label(
        text=f"[b]{value}[/b]" if is_title else value,
        font_size=26,
        markup=is_title,
        size_hint=(None, None),
        size=(dp(width), dp(34)),
        halign="left",
        valign="middle",
    )
    label.text_size = label.size
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label
