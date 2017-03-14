
# Blueprint creation

from flask      import Blueprint

from app.data.game.game_service import DdGameService


main = Blueprint( "main", __name__ )
main.game_service = DdGameService()

from .                  import views, errors
from app.data.models    import DdPermission


@main.app_context_processor
def InjectPermissions():
    return dict( Permissions=DdPermission )
