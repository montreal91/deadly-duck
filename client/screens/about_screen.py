"""
Created August 18, 2026

@author montreal91
"""
from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen

from client.constants import button_size
from client.widgets.factories import make_label
from configuration.config_game import MiscConstants


class AboutScreen(Screen):
    def __init__(self, **kwargs):
        super(AboutScreen, self).__init__(**kwargs)

        root = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint=(None, None),
        )
        layout.bind(minimum_size=layout.setter("size"))

        title_label = make_label("[b]Legends of the Courts[/b]", font_size=50)
        title_label.markup = True
        title_label.halign = "center"
        layout.add_widget(title_label)

        genre_label = make_label("A jRPG-flavoured Tennis Manager", font_size=30)
        genre_label.halign = "center"
        layout.add_widget(genre_label)

        version_label = make_label(
            f"Version: [b]{MiscConstants.CURRENT_VERSION.value}[/b]",
            font_size=25,
        )
        version_label.halign = "center"
        version_label.markup = True
        layout.add_widget(version_label)

        author_title_label = make_label("Author: [b]Alexander Nefedov[/b]", font_size=25)
        author_title_label.halign = "center"
        author_title_label.markup = True
        layout.add_widget(author_title_label)

        layout.add_widget(Widget(size_hint_y=None, height=20))

        back_button = Button(
            text="Back",
            font_size=30,
            size_hint=(None, None),
            size=button_size,
        )
        back_button.bind(on_press=_back_to_main_screen)
        layout.add_widget(back_button)

        root.add_widget(layout)
        self.add_widget(root)


def _back_to_main_screen(_):
    App.get_running_app().switch_to_main(None)
