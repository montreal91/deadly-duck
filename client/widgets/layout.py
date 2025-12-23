"""
Created December 22, 2025

@author montreal91
"""
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


def make_default_layout(title):
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


class ThreeColLayout:
    def __init__(self, root, col_list):
        self.root = root
        self.col_list = col_list

    @property
    def left_col(self):
        return self.col_list[0]

    @property
    def center_col(self):
        return self.col_list[1]

    @property
    def right_col(self):
        return self.col_list[2]


def make_three_column_layout(
        title_text,
        left_width_hint,
        center_width_hint,
        right_width_hint
):
    root = AnchorLayout(anchor_x="left", anchor_y="top")

    container = BoxLayout(
        orientation="vertical",
        padding=20,
        spacing=20,
        size_hint=(1, 1),
    )
    root.add_widget(container)

    title = Label(
        text=title_text,
        font_size=48,
        size_hint=(1, None),
        height=80,
        halign="left",
        valign="middle",
    )
    title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    container.add_widget(title)

    content = BoxLayout(
        orientation="horizontal",
        spacing=20,
        size_hint=(1, 1),
    )

    columns = []

    left_col = BoxLayout(
        orientation="vertical",
        padding=30,
        spacing=10,
        size_hint=(left_width_hint, 1),
    )
    columns.append(left_col)
    content.add_widget(left_col)

    center_col = BoxLayout(
        orientation="vertical",
        padding=30,
        spacing=10,
        size_hint=(center_width_hint, 1),
    )
    columns.append(center_col)
    content.add_widget(center_col)

    right_col = BoxLayout(
        orientation="vertical",
        padding=30,
        spacing=10,
        size_hint=(right_width_hint, 1),
        width=right_width_hint,
    )
    columns.append(right_col)
    content.add_widget(right_col)

    container.add_widget(content)

    return ThreeColLayout(root, columns)
