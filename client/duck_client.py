"""
Created May 20, 2024

@author montreal91
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import NoTransition
from kivy.clock import Clock
from kivy.config import Config

from client.splash_screen import SplashScreen
from client.main_screen import MainScreen


Config.set("graphics", "fullscreen", "auto")


class DuckClientApp(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.splash_screen = SplashScreen(name="splash")
        self.main_screen = MainScreen(name="main")

        self.sm.add_widget(self.splash_screen)
        self.sm.add_widget(self.main_screen)

        Clock.schedule_once(self.switch_to_main, timeout=3)

        return self.sm

    def switch_to_main(self, dt):
        self.sm.current = "main"
