
from flask import Blueprint

from app.data.game.game_service import DdGameService

game = Blueprint("game", __name__)
game.selected_players = {}
game.contexts = {}
game.service = DdGameService()

from app.game import old_views
