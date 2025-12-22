"""
Created May 20, 2024

@author montreal91
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import NoTransition
from kivy.clock import Clock

from client.club_selection_screen import ClubSelectionScreen
from client.game_screen import GameScreen
from client.load_story_screen import LoadStoryScreen
from client.splash_screen import SplashScreen
from client.main_screen import MainScreen
from client.story_name_screen import StoryNameScreen

class DuckClientApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = None
        self.main_screen = None
        self.splash_screen = None
        self.story_name_screen = None
        self._club_selection_screen = None
        self._load_story_screen = None

        self.sm = None

    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.splash_screen = SplashScreen(name="splash")
        self.main_screen = MainScreen(name="main")
        self.game_screen = GameScreen(name="game")
        self.story_name_screen = StoryNameScreen(name="story_name")
        self._club_selection_screen = ClubSelectionScreen(name="club_selection")
        self._load_story_screen = LoadStoryScreen(name="load_story")

        self.sm.add_widget(self.splash_screen)
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.game_screen)
        self.sm.add_widget(self.story_name_screen)
        self.sm.add_widget(self._club_selection_screen)
        self.sm.add_widget(self._load_story_screen)

        Clock.schedule_once(self.switch_to_main, timeout=1)

        return self.sm

    def switch_to_main(self, _):
        self.sm.current = "main"

    def start_game(self):
        self.sm.current = "game"
        self.game_screen.init_game_data()
        self.game_screen.update()

    def switch_to_load_story(self):
        self.sm.current = "load_story"
        self._load_story_screen.update_saved_games()

    def switch_to_story_name(self):
        self.sm.current = "story_name"
        self.story_name_screen.cleanup()

    def switch_to_club_selection(self):
        self.sm.current = "club_selection"
        self._club_selection_screen.cleanup()
