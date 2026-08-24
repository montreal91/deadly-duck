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

_ACTION_WIDTH = 350
_ACTION_HEIGHT = 50
_SAVE_BUTTON_MAX_WIDTH = 350
_INFO_LABEL_MAX_WIDTH = 520


class LoadStoryScreen(Screen):
    def __init__(self, **kwargs):
        super(LoadStoryScreen, self).__init__(**kwargs)

        self._game_service = get_application_context().game_service
        self._saved_games_buttons = []
        self._selected_save = None

        self._layout = make_three_column_layout(
            title_text="Continue Story",
            left_width_hint=0.25,
            center_width_hint=0.35,
            right_width_hint=0.4,
        )

        self._save_list = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None),
        )
        self._save_list.bind(minimum_height=self._save_list.setter("height"))

        save_scroll = ScrollView(
            do_scroll_x=False,
            size_hint=(1, 1),
        )
        save_scroll.add_widget(self._save_list)
        self._layout.center_col.add_widget(save_scroll)

        self._continue_button = Button(
            text="Continue",
            font_size=30,
            size_hint=(None, None),
            height=dp(_ACTION_HEIGHT),
            disabled=True,
        )
        self._bind_width_to_column(
            self._continue_button,
            self._layout.left_col,
            _ACTION_WIDTH,
        )
        self._continue_button.bind(on_press=self._on_continue)
        self._layout.left_col.add_widget(self._continue_button)

        self._back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            height=dp(_ACTION_HEIGHT),
        )
        self._bind_width_to_column(
            self._back_button,
            self._layout.left_col,
            _ACTION_WIDTH,
        )
        self._back_button.bind(on_press=_back_to_main_screen)
        self._layout.left_col.add_widget(self._back_button)
        self._layout.left_col.add_widget(Widget())

        self.add_widget(self._layout.root)

    def update_saved_games(self):
        self._save_list.clear_widgets()
        self._saved_games_buttons = []
        self._selected_save = None
        self._continue_button.disabled = True

        stories = self._game_service.get_saved_games().names
        for story in stories:
            button = self._make_load_game_button(story)
            self._save_list.add_widget(button)
            self._saved_games_buttons.append(button)

        self._render_save_info(None)

    def _make_load_game_button(self, game_name):
        button = ToggleButton(
            text=game_name,
            group="games",
            size_hint=(None, None),
            height=dp(_ACTION_HEIGHT),
        )
        self._bind_width_to_column(
            button,
            self._layout.center_col,
            _SAVE_BUTTON_MAX_WIDTH,
        )
        button.game_name = game_name
        button.bind(on_press=self._on_select)
        return button

    def _on_select(self, instance):
        if instance.state != "down":
            return

        self._selected_save = instance.game_name
        self._continue_button.disabled = False
        self._render_save_info(instance.game_name)

    def _on_continue(self, _):
        if self._selected_save is None:
            print("No game is selected")
            return

        GameContext.get_instance().game_name = self._selected_save
        GameContext.get_instance().club_id = self._game_service.get_manager_club_id(
            self._selected_save
        )

        App.get_running_app().start_game()

    def _render_save_info(self, game_name):
        self._layout.right_col.clear_widgets()

        if game_name is None:
            self._layout.right_col.add_widget(_make_info_title(
                "Select a story",
                self._layout.right_col,
            ))
            self._layout.right_col.add_widget(Widget())
            return

        self._layout.right_col.add_widget(_make_info_title(
            game_name,
            self._layout.right_col,
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
