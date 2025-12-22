"""
Created December 22, 2025

@author montreal91
"""
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


def make_default_layouts(title):
    root = AnchorLayout(anchor_x="left", anchor_y="top")

    container = BoxLayout(
        orientation="vertical",
        padding=[20, 20, 20, 20],
        spacing=20,
        size_hint=(None, None),
    )
    container.bind(minimum_size=container.setter("size"))

    menu = BoxLayout(orientation="vertical", spacing=20, size_hint=(None, None))

    menu.title_label = Label(text=title, font_size=50, size_hint=(None, None))
    menu.title_label.bind(texture_size=menu.title_label.setter("size"))

    menu.bind(minimum_size=menu.setter("size"))

    container.add_widget(menu.title_label)
    container.add_widget(menu)

    root.add_widget(container)
    return menu, root
