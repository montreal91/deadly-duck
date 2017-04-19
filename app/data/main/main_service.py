
from app.data.main.friendship import DdDaoFriendship
from app.data.main.message import DdDaoMessage
from app.data.main.user import DdDaoUser

class Placeholder:
    pass


class DdMainService( object ):
    def __init__( self ):
        super( DdMainService, self ).__init__()

        self._dao_friendship = DdDaoFriendship()
        self._dao_message = DdDaoMessage()
        self._dao_user = DdDaoUser()


    def AcceptFriendRequest( self, request=None ):
        if not self._dao_friendship.IsFriendshipExists( u1_pk=request.from_pk, u2_pk=request.to_pk ):
            friendship = self._dao_friendship.CreateFriendship( 
                from_pk=request.from_pk,
                to_pk=request.to_pk
                )
            self._dao_friendship.SaveFriendship( friendship=friendship )
            return True
        else:
            return False

    def CreateMessage( self, from_pk=0, to_pk=0, subject="", text="" ):
        return self._dao_message.CreateMessage( 
            from_pk=from_pk,
            to_pk=to_pk,
            subject=subject,
            text=text
        )

    def FindUserByPartOfUsername( self, search_token="" ):
        return self._dao_user.FindUserByPartOfUsername( search_token=search_token )

    def GetAllFriendsForUser( self, user_pk ):
        return self._dao_user.GetAllFriendsForUser( user_pk=user_pk )

    def GetAllIncomingMessages( self, user_pk=0 ):
        return self._dao_message.GetAllIncomingMessages( user_pk=user_pk )

    def GetAllOutcomingMessages( self, user_pk=0 ):
        return self._dao_message.GetAllOutcomingMessages( user_pk=user_pk )

    def GetFriendRequestByPk( self, request_pk=0 ):
        return self._dao_friendship.GetFriendRequestByPk( request_pk=request_pk )

    def GetFriendshipObject( self, u1_pk=0, u2_pk=0 ):
        return self._dao_friendship.GetFriendshipObject( u1_pk=u1_pk, u2_pk=u2_pk )

    def GetIncomingFriendRequests( self, user_pk=0 ):
        return self._dao_friendship.GetIncomingFriendRequests( user_pk=user_pk )

    def GetMessageByPk( self, pk ):
        return self._dao_message.GetMessageByPk( pk )

    def GetNumberOfActiveFriendRequests( self, user_one_pk=0, user_two_pk=0 ):
        return self._dao_friendship.GetNumberOfActiveFriendRequests( 
            user_one_pk=user_one_pk,
            user_two_pk=user_two_pk
        )

    def GetNumberOfFriends( self, user_pk=0 ):
        return self._dao_user.GetNumberOfFriends( user_pk=user_pk )

    def GetNumberOfIncomingFriendRequests( self, user_pk=0 ):
        return self._dao_friendship.GetNumberOfIncomingFriendRequests( user_pk=user_pk )

    def GetNumberOfOutcomingFriendRequests( self, user_pk=0 ):
        return self._dao_friendship.GetNumberOfOutcomingFriendRequests( user_pk=user_pk )

    def GetNumberOfUsers( self ):
        return self._dao_user.GetNumberOfUsers()

    def GetOutcomingFriendRequests( self, user_pk=0 ):
        return self._dao_friendship.GetOutcomingFriendRequests( user_pk=user_pk )

    def GetTotalNumberOfIncomingNewMessages( self, user_pk=0 ):
        return self._dao_message.GetTotalNumberOfIncomingNewMessages( user_pk=user_pk )

    def GetUserByUsername( self, username="" ):
        return self._dao_user.GetUserByUsername( username=username )

    def IsFriendshipPossible( self, user_one_pk=0, user_two_pk=0 ):
        if user_one_pk == user_two_pk:
            return False
        if self.GetNumberOfActiveFriendRequests( user_one_pk=user_one_pk, user_two_pk=user_two_pk ) > 0:
            return False
        if self._dao_friendship.IsFriendshipExists( u1_pk=user_one_pk, u2_pk=user_two_pk ):
            return False
        return True

    def IsMessagingPossible( self, user1_pk=0, user2_pk=0 ):
        return self._dao_friendship.IsFriendshipExists( u1_pk=user1_pk, u2_pk=user2_pk )

    def MakeFriendRequest( self, from_pk=0, to_pk=0, message="" ):
        if self.GetNumberOfActiveFriendRequests( user_one_pk=from_pk, user_two_pk=to_pk ) > 0:
            return False
        else:
            request = self._dao_friendship.CreateFriendRequest( 
                from_pk=from_pk,
                to_pk=to_pk,
                message=message
            )
            self._dao_friendship.SaveFriendRequest( friend_request=request )
            return True

    def SaveFriendRequest( self, friend_request=None ):
        self._dao_friendship.SaveFriendRequest( friend_request=friend_request )

    def SaveFriendship( self, friendship_object=None ):
        self._dao_friendship.SaveFriendship( friendship=friendship_object )

    def SaveMessage( self, message=None ):
        self._dao_message.SaveMessage( message=message )
