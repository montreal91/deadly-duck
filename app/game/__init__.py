
from flask import Blueprint

game = Blueprint( "game", __name__ )
game.selected_players = {}

from . import views
