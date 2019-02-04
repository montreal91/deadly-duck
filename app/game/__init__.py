
from flask import Blueprint

from app.data.game.game_service import DdGameService

game = Blueprint("game", __name__)
game.service = DdGameService()

from app.game import views
