"""
Created December 22, 2025

@author montreal91
"""
from kivy.uix.textinput import TextInput


class AlphanumericTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        filtered = ''.join(ch for ch in substring if ch.isalnum())
        super().insert_text(filtered, from_undo=from_undo)
