"""
Created May 20, 2024

@author montreal91
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        label = Label(text="Main Screen", font_size=50)
        exit_button = Button(
            text="Exit",
            font_size=30,
            size_hint=(None, None),
            size=(200, 50)
        )

        exit_button.bind(on_press=self.exit_app)
        layout.add_widget(label)
        layout.add_widget(exit_button)
        self.add_widget(layout)

    def exit_app(self, instance):
        App.get_running_app().stop()
