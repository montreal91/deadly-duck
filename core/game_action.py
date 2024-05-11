"""
Different game actions.

Created May 11, 2024

@author montreal91
"""

class ObjectType(Enum):
    WORLD = 0
    PLAYER = 1
    CLUB = 2

class GameAction:
    pass
    # class Type(Enum):
    #     NEXT_DAY = 0

class NextDay(GameAction):
    def __init__(self, game_id, manager_id, club_id):
        self.game_id = game_id
        self.manager_id = manager_id
        self.club_id = club_id


# class SelectPlayer
