"""
Created August 17, 2026

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

_DEFAULT_COL_WIDTH = 100
_PLAYER_ID_COL_WIDTH = 35
_PLAYER_NAME_COL_WIDTH = 180


class RosterManagementTable:
    def __init__(self):
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
            self._root.add_widget(_make_player_row(player))


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


def _make_player_row(player):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(36),
    )

    row.add_widget(_make_cell(str(player.player_id), width=_PLAYER_ID_COL_WIDTH))
    row.add_widget(_make_cell(player.name, width=_PLAYER_NAME_COL_WIDTH))
    row.add_widget(_make_cell(str(player.level)))
    row.add_widget(_make_cell(str(player.age)))
    row.add_widget(_make_cell(str(player.technique)))
    row.add_widget(_make_cell(str(player.endurance)))
    row.add_widget(_make_cell(_format_contract_cost(player.contract_cost)))

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


def _format_contract_cost(contract_cost):
    if contract_cost is None:
        return "Signed"
    return str(contract_cost)


def _get_col_width(title):
    if title == "#":
        return _PLAYER_ID_COL_WIDTH
    if title == "Name":
        return _PLAYER_NAME_COL_WIDTH
    return _DEFAULT_COL_WIDTH
