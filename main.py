"""
Created May 20, 2024

@author montreal91
"""
from kivy.config import Config

from persistence.migration_history import init_db

# Needs to be here to take an effect
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "borderless", "1")
Config.set("graphics", "resizable", "0")


if __name__ == '__main__':
    from client import DuckClientApp

    init_db("data/duck.db")

    DuckClientApp().run()
