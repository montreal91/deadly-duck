"""
Created December 22, 2025

@author montreal91
"""
class GameContext:
    _instance = None

    @staticmethod
    def get_instance():
        if GameContext._instance is None:
            GameContext._instance = GameContext()
        return GameContext._instance

    @staticmethod
    def new_context():
        _instance = GameContext()
        return _instance

    def __init__(self):
        self.club_id = None
        self.game_name = None
