"""
Created August 17, 2026

@author montreal91
"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

_PLAYER_ID_COL_WIDTH = 0.05
_PLAYER_NAME_COL_WIDTH = 0.18
_AGE_COL_WIDTH = 0.06
_LEVEL_COL_WIDTH = 0.06
_EXPERIENCE_COL_WIDTH = 0.12
_TECHNIQUE_COL_WIDTH = 0.09
_ENDURANCE_COL_WIDTH = 0.09
_COACH_COL_WIDTH = 0.07
_COST_COL_WIDTH = 0.10
_ACTION_COL_WIDTH = 0.18


class PracticeTable:
    def __init__(self, on_select_coach):
        self._on_select_coach = on_select_coach
        self._root = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(8), dp(8)),
            spacing=dp(4),
        )
        self._header = _PracticeTableHeader()
        self._root.add_widget(self._header.widget)
        self._root.bind(minimum_height=self._root.setter("height"))

    @property
    def widget(self):
        return self._root

    def update(self, players):
        self._root.clear_widgets()
        self._root.add_widget(self._header.widget)

        for player in players:
            self._root.add_widget(_make_player_row(player, self._on_select_coach))


class _PracticeTableHeader:
    def __init__(self):
        self._root = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )

        cols = (
            "#",
            "Name",
            "Age",
            "Level",
            "Experience",
            "Technique",
            "Endurance",
            "Coach",
            "Cost",
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


def _make_player_row(player, on_select_coach):
    row = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(36),
    )

    row.add_widget(_make_cell(str(player.pos), width=_PLAYER_ID_COL_WIDTH))
    row.add_widget(_make_cell(player.name, width=_PLAYER_NAME_COL_WIDTH))
    row.add_widget(_make_cell(str(player.age), width=_AGE_COL_WIDTH))
    row.add_widget(_make_cell(str(player.level), width=_LEVEL_COL_WIDTH))
    row.add_widget(_make_cell(
        f"{player.experience}/{player.next_level_experience}",
        width=_EXPERIENCE_COL_WIDTH,
    ))
    row.add_widget(_make_cell(str(player.technique), width=_TECHNIQUE_COL_WIDTH))
    row.add_widget(_make_cell(str(player.endurance), width=_ENDURANCE_COL_WIDTH))
    row.add_widget(_make_cell(str(player.coach_level), width=_COACH_COL_WIDTH))
    row.add_widget(_make_cell(str(player.practice_cost), width=_COST_COL_WIDTH))
    row.add_widget(_make_action_cell(player.player_id, on_select_coach))

    return row


def _make_cell(value, width, is_header=False):
    cell = Label(
        text=value,
        markup=is_header,
        halign="left",
        valign="middle",
        size_hint_x=width,
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
    if title == "Age":
        return _AGE_COL_WIDTH
    if title == "Level":
        return _LEVEL_COL_WIDTH
    if title == "Experience":
        return _EXPERIENCE_COL_WIDTH
    if title == "Technique":
        return _TECHNIQUE_COL_WIDTH
    if title == "Endurance":
        return _ENDURANCE_COL_WIDTH
    if title == "Coach":
        return _COACH_COL_WIDTH
    if title == "Cost":
        return _COST_COL_WIDTH
    if title == "Action":
        return _ACTION_COL_WIDTH
    raise Exception("Unknown practice table column.")


def _make_action_cell(player_id, on_select_coach):
    cell = BoxLayout(
        orientation="horizontal",
        spacing=dp(3),
        size_hint_x=_ACTION_COL_WIDTH,
    )

    for coach_index in range(4):
        cell.add_widget(_make_coach_button(
            player_id=player_id,
            coach_index=coach_index,
            on_select_coach=on_select_coach,
        ))

    return cell


def _make_coach_button(player_id, coach_index, on_select_coach):
    button = Button(
        text=str(coach_index),
        size_hint=(1, None),
        height=dp(35),
    )
    button.player_id = player_id
    button.coach_index = coach_index
    button.on_select_coach = on_select_coach
    button.bind(on_press=_on_select_coach)
    return button


def _on_select_coach(button):
    button.on_select_coach(button.player_id, button.coach_index)
