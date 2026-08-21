"""
Created August 20, 2026

@author montreal91
"""
from core.player import Player


def make_player_from_row(row) -> Player:
    player = Player(
        first_name=row["first_name"],
        second_name=row["second_name"],
        last_name=row["last_name"],
        technique=row["technique"],
        endurance=row["endurance"],
        age=row["age"],
    )
    player._player_id = row["player_id"]
    player._exhaustion = row["exhaustion"]
    player._experience = row["experience"]
    player._skill_points = row["skill_points"]
    player._current_stamina = row["current_stamina"]
    player._reputation = row["reputation"]
    return player
