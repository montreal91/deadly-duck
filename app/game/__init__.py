
from flask import Blueprint

game = Blueprint( "game", __name__ )
game.selected_players = {}
game.contexts = {}

from . import views
