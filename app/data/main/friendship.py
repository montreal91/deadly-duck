
from datetime           import datetime

from sqlalchemy         import text

from app                import db

from app.custom_queries import EXISTING_FRIENDSHIP_SQL
from app.custom_queries import FRIENDSHIP_SQL
from app.custom_queries import INCOMING_FRIEND_REQUESTS_SQL
from app.custom_queries import NUMBER_OF_ACTIVE_FRIEND_REQUESTS_SQL
from app.custom_queries import NUMBER_OF_INCOMING_FRIEND_REQUESTS_SQL
from app.custom_queries import NUMBER_OF_OUTCOMING_FRIEND_REQUESTS_SQL
from app.custom_queries import OUTCOMING_FRIEND_REQUESTS_SQL

class DdFriendRequest( db.Model ):
    __tablename__ = "friend_requests"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable

    from_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable
    to_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable

    timestamp_dt = db.Column( db.DateTime, default=datetime.utcnow() ) # @UndefinedVariable
    is_accepted = db.Column( db.Boolean, default=False ) # @UndefinedVariable
    is_rejected = db.Column( db.Boolean, default=False ) # @UndefinedVariable
    message_txt = db.Column( db.Text ) # @UndefinedVariable

    def __repr__( self ):
        return "<FriendRequest #{pk:d} from {from_pk:d} to {to_pk:d}>".format( 
            pk=self.pk,
            from_pk=self.from_pk,
            to_pk=self.to_pk
        )

class DdFriendship( db.Model ):
    __tablename__ = "friendship"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable

    friend_one_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable
    friend_two_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable

    is_active = db.Column( db.Boolean, default=True ) # @UndefinedVariable
    timestamp_dt = db.Column( db.DateTime, default=datetime.utcnow() ) # @UndefinedVariable

    def __repr__( self ):
        return "<Friendship between {one:d} and {two:d}>".format( 
            one=self.friend_one_pk,
            two=self.friend_two_pk
        )


class DdDaoFriendship( object ):
    def CreateFriendRequest( self, from_pk=0, to_pk=0, message="" ):
        """
        Creates new DdFriendRequest object.
        :param from_pk: primary key of user who sends friend request
        :param to_pk: primary key of user who recieves friend request
        """
        request = DdFriendRequest()
        request.from_pk = from_pk
        request.to_pk = to_pk
        request.message_txt = message
        return request

    def CreateFriendship( self, from_pk=0, to_pk=0 ):
        friendship = DdFriendship()
        friendship.friend_one_pk = from_pk
        friendship.friend_two_pk = to_pk
        return friendship

    def GetFriendRequestByPk( self, request_pk=0 ):
        """
        Gets Friend Request by primary key.
        If there is no such request in the database, raises 404 error.
        :param request_pk: primary key of request
        """
        return DdFriendRequest.query.get_or_404( request_pk )

    def GetFriendshipObject( self, u1_pk=0, u2_pk=0 ):
        return DdFriendship.query.from_statement( 
            text( FRIENDSHIP_SQL ).params( 
                u1_pk=u1_pk,
                u2_pk=u2_pk
            )
        ).first()


    def GetIncomingFriendRequests( self, user_pk=0 ):
        return db.engine.execute( # @UndefinedVariable
            text( INCOMING_FRIEND_REQUESTS_SQL ).params( 
                user_pk=user_pk
            )
        ).fetchall() # @UndefinedVariable


    def GetNumberOfActiveFriendRequests( self, user_one_pk=0, user_two_pk=0 ):
        query_res = db.engine.execute( # @UndefinedVariable
            text( NUMBER_OF_ACTIVE_FRIEND_REQUESTS_SQL ).params( 
                user_one_pk=user_one_pk,
                user_two_pk=user_two_pk
            )
        ).first()
        return query_res["number_of_active_friend_requests"] # @UndefinedVariable


    def GetNumberOfIncomingFriendRequests( self, user_pk=0 ):
        query_res = db.engine.execute( # @UndefinedVariable
            text( NUMBER_OF_INCOMING_FRIEND_REQUESTS_SQL ).params( 
                user_pk=user_pk,
            )
        ).first()
        return query_res["incoming_friend_requests"] # @UndefinedVariable

    def GetNumberOfOutcomingFriendRequests( self, user_pk=0 ):
        query_res = db.engine.execute( # @UndefinedVariable
            text( NUMBER_OF_OUTCOMING_FRIEND_REQUESTS_SQL ).params( user_pk=user_pk ) ).first() # @UndefinedVariable
        return query_res["outcoming_friend_requests"] # @UndefinedVariable

    def GetOutcomingFriendRequests( self, user_pk=0 ):
        return db.engine.execute( # @UndefinedVariable
            text( OUTCOMING_FRIEND_REQUESTS_SQL ).params( 
                user_pk=user_pk
            )
        ).fetchall() # @UndefinedVariable

    def IsFriendshipExists( self, u1_pk=0, u2_pk=0 ):
        query_res = db.engine.execute( # @UndefinedVariable
            text( EXISTING_FRIENDSHIP_SQL ).params( 
                u1_pk=u1_pk,
                u2_pk=u2_pk
            )
        ).first()

        return query_res["number_of_existing_friendships"] > 0

    def SaveFriendRequest( self, friend_request=None ):
        db.session.add( friend_request ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SaveFriendRequests( self, friend_requests=[] ):
        db.session.add_all( friend_requests ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SaveFriendship( self, friendship=None ):
        db.session.add( friendship ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable
