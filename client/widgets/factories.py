"""
Created December 23, 2025

@author montreal91
"""
from kivy.uix.label import Label


def make_label(text=" ", font_size=30):
    label = Label(text=text, font_size=font_size, size_hint=(None, None))
    label.bind(texture_size=label.setter("size"))
    return label
