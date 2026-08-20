"""
Created August 17, 2026

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

_DEFAULT_COL_WIDTH = 100
_PLAYER_ID_COL_WIDTH = 35
_PLAYER_NAME_COL_WIDTH = 180
_ACTION_COL_WIDTH = 230


class RosterManagementTable:
    def __init__(self, on_sign_player, on_fire_player, on_show_player_details):
        self._on_sign_player = on_sign_player
        self._on_fire_player = on_fire_player
        self._on_show_player_details = on_show_player_details
        self._root = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(8), dp(8)),
            spacing=dp(4),
        )
        self._header = _RosterManagementTableHeader()
        self._root.add_widget(self._header.widget)
        self._root.bind(minimum_height=self._root.setter("height"))

    @property
    def widget(self):
        return self._root

    def update(self, players):
        self._root.clear_widgets()
        self._root.add_widget(self._header.widget)

        for player in players:
            self._root.add_widget(_make_player_row(
                player,
                self._on_sign_player,
                self._on_fire_player,
                self._on_show_player_details,
            ))


class _RosterManagementTableHeader:
    def __init__(self):
        self._root = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )

        cols = (
            "#",
            "Name",
            "Level",
            "Age",
            "Technique",
            "Endurance",
            "Contract",
            "Action",
        )

        for title in cols:
            self._root.add_widget(_make_cell(
                f"[b]{title}[/b]",
                width=_get_col_width(title),
                is_header=True,
            ))

    @property
    def widget(self):
        return self._root


def _make_player_row(
        player,
        on_sign_player,
        on_fire_player,
        on_show_player_details,
):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(36),
    )

    row.add_widget(_make_cell(str(player.pos), width=_PLAYER_ID_COL_WIDTH))
    row.add_widget(_make_cell(player.name, width=_PLAYER_NAME_COL_WIDTH))
    row.add_widget(_make_cell(str(player.level)))
    row.add_widget(_make_cell(str(player.age)))
    row.add_widget(_make_cell(str(player.technique)))
    row.add_widget(_make_cell(str(player.endurance)))
    row.add_widget(_make_cell(player.contract_status))
    row.add_widget(_make_action_cell(
        player,
        on_sign_player,
        on_fire_player,
        on_show_player_details,
    ))

    return row


def _make_cell(value, width=_DEFAULT_COL_WIDTH, is_header=False):
    cell = Label(
        text=value,
        markup=is_header,
        halign="left",
        valign="middle",
        size_hint_x=None,
        width=dp(width),
        shorten=True,
        shorten_from="right",
    )
    cell.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    return cell


def _get_col_width(title):
    if title == "#":
        return _PLAYER_ID_COL_WIDTH
    if title == "Name":
        return _PLAYER_NAME_COL_WIDTH
    if title == "Action":
        return _ACTION_COL_WIDTH
    return _DEFAULT_COL_WIDTH


def _make_fire_button(player_id, on_fire_player):
    button = Button(
        text="Fire",
        size_hint=(None, None),
        size=(dp(70), dp(35)),
    )
    button.player_id = player_id
    button.on_fire_player = on_fire_player
    button.bind(on_press=_on_fire)
    return button


def _make_sign_button(player_id, on_sign_player):
    button = Button(
        text="Sign",
        size_hint=(None, None),
        size=(dp(70), dp(35)),
    )
    button.player_id = player_id
    button.on_sign_player = on_sign_player
    button.bind(on_press=_on_sign)
    return button


def _make_details_button(player_id, on_show_player_details):
    button = Button(
        text="Details",
        size_hint=(None, None),
        size=(dp(80), dp(35)),
    )
    button.player_id = player_id
    button.on_show_player_details = on_show_player_details
    button.bind(on_press=_on_details)
    return button


def _make_action_cell(
        player,
        on_sign_player,
        on_fire_player,
        on_show_player_details,
):
    cell = BoxLayout(
        orientation="horizontal",
        spacing=dp(4),
        size_hint_x=None,
        width=dp(_ACTION_COL_WIDTH),
    )

    cell.add_widget(Widget())
    cell.add_widget(_make_details_button(
        player.player_id,
        on_show_player_details,
    ))

    if player.contract_cost is not None:
        cell.add_widget(_make_sign_button(player.player_id, on_sign_player))

    cell.add_widget(_make_fire_button(player.player_id, on_fire_player))
    cell.add_widget(Widget())

    return cell


def _on_fire(button):
    button.on_fire_player(button.player_id)


def _on_sign(button):
    button.on_sign_player(button.player_id)


def _on_details(button):
    button.on_show_player_details(button.player_id)
