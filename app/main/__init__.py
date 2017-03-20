
# Blueprint creation

from flask      import Blueprint

from app.data.game.game_service import DdGameService
from app.data.main.main_service import DdMainService


main = Blueprint( "main", __name__ )
main.service = DdMainService()
main.game_service = DdGameService()


from .                  import views, errors
from app.data.main.role import DdPermission


@main.app_context_processor
def InjectPermissions():
    return dict( Permissions=DdPermission )

@main.app_context_processor
def NumericFriendFunctions():
    def GetNumberOfIncomingFriendRequests( user_pk=0 ):
        return main.service.GetNumberOfIncomingFriendRequests( user_pk=user_pk )

    def GetNumberOfOutcomingFriendRequests( user_pk=0 ):
        return main.service.GetNumberOfOutcomingFriendRequests( user_pk=user_pk )


    def GetNumberOfFriends( user_pk=0 ):
        return main.service.GetNumberOfFriends( user_pk=user_pk )

    return dict( 
        GetNumberOfIncomingFriendRequests=GetNumberOfIncomingFriendRequests,
        GetNumberOfOutcomingFriendRequests=GetNumberOfOutcomingFriendRequests,
        GetNumberOfFriends=GetNumberOfFriends
    )
