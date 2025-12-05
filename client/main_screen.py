"""
Created May 20, 2024

@author montreal91
"""
from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


button_size = (350, 50)


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Use AnchorLayout to align content to the top-left corner
        anchor_layout = AnchorLayout(anchor_x='left', anchor_y='top')

        # Create a vertical BoxLayout for the menu
        layout = BoxLayout(
            orientation='vertical',
            padding=[20, 20, 20, 20],
            spacing=20,
            size_hint=(None, None)
        )
        # Ensure the layout adjusts its height based on its content
        layout.bind(minimum_height=layout.setter('height'))

        # Title Label
        title = Label(
            text='Legends of the Court',
            font_size=50,
            size_hint=(1, None),
            # width=500,
            height=100,
            halign='right',
            valign='middle',
            text_size=(850, 100),  # Match text_size with the size of the label
            # padding_x=20,
            # padding_y=20,
        )
        # title.bind(size=title.setter('text_size'))  # Ensure the text is aligned properly within the label
        layout.add_widget(title)

        # Story Button
        story_button = Button(text='Story', font_size=30, size_hint=(None, None), size=button_size)
        story_button.bind(on_press=self.show_story)
        layout.add_widget(story_button)

        # Credits Button
        credits_button = Button(text='Credits', font_size=30, size_hint=(None, None), size=button_size)
        credits_button.bind(on_press=self.show_credits)
        layout.add_widget(credits_button)

        # Exit Button
        exit_button = Button(text='Exit', font_size=30, size_hint=(None, None), size=button_size)
        exit_button.bind(on_press=self.exit_app)
        layout.add_widget(exit_button)

        # Add the BoxLayout to the AnchorLayout
        anchor_layout.add_widget(layout)

        # Add the AnchorLayout to the screen
        self.add_widget(anchor_layout)

    def show_story(self, instance):
        print("Story button pressed")
        # Here you could switch to a story screen or display a story dialog

    def show_credits(self, instance):
        print("Credits button pressed")
        # Here you could switch to a credits screen or display credits information

    @staticmethod
    def exit_app(instance):
        App.get_running_app().stop()
