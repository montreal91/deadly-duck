"""
Created May 20, 2024

@author montreal91
"""
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super(SplashScreen, self).__init__(**kwargs)
        self.add_widget(Label(text="Welcome to the Courts", font_size=50))
