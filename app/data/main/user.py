
import hashlib
from datetime           import datetime


from flask              import current_app, request
from flask_login        import AnonymousUserMixin, UserMixin
from itsdangerous       import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import text
from werkzeug.security  import check_password_hash, generate_password_hash

from app                import db
from app.custom_queries import FRIENDS_SQL
from app.custom_queries import NUMBER_OF_FRIENDS_SQL
from app.data.main.role import DdRole, DdPermission


class DdUser( UserMixin, db.Model ):
    __tablename__ = "users"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    username = db.Column( db.String( 64 ), unique=True, index=True ) # @UndefinedVariable
    email = db.Column( db.String( 64 ), unique=True, index=True ) # @UndefinedVariable
    role_pk = db.Column( db.Integer, db.ForeignKey( "roles.pk" ) ) # @UndefinedVariable
    password_hash = db.Column( db.String( 128 ) ) # @UndefinedVariable
    confirmed = db.Column( db.Boolean, default=False ) # @UndefinedVariable
    name = db.Column( db.String( 64 ) ) # @UndefinedVariable
    location = db.Column( db.String( 64 ) ) # @UndefinedVariable
    about_me = db.Column( db.Text() ) # @UndefinedVariable
    member_since = db.Column( db.DateTime(), default=datetime.utcnow ) # @UndefinedVariable
    last_seen = db.Column( db.DateTime(), default=datetime.utcnow ) # @UndefinedVariable
    avatar_hash = db.Column( db.String( 32 ) ) # @UndefinedVariable
    posts = db.relationship( "DdPost", backref="author", lazy="dynamic" ) # @UndefinedVariable

    managed_club_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ) ) # @UndefinedVariable
    current_season_n = db.Column( db.Integer, default=1 ) # @UndefinedVariable
    current_day_n = db.Column( db.Integer, default=0 ) # @UndefinedVariable


    def __init__( self, **kwargs ):
        super( DdUser, self ).__init__( **kwargs )
        if self.role is None:
            if self.email == current_app.config["FLASKY_ADMIN"]:
                self.role = DdRole.query.filter_by( permissions=0xff ).first() # @UndefinedVariable
            if self.role is None:
                self.role = DdRole.query.filter_by( default=True ).first() # @UndefinedVariable
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5( 
                    self.email.encode( "utf-8" )
                ).hexdigest()


    @property
    def password( self ):
        raise AttributeError( "password is not a readable attribute" )


    @password.setter
    def password( self, password ):
        self.password_hash = generate_password_hash( password )


    def VerifyPassword( self, password ):
        return check_password_hash( self.password_hash, password )


    def GenerateConfirmationToken( self, expiration=3600 ):
        s = Serializer( current_app.config["SECRET_KEY"], expiration )
        return s.dumps( { "confirm": self.pk } )


    # TODO: put many of these methods into DdDaoUser class
    def Confirm( self, token ):
        s = Serializer( current_app.config["SECRET_KEY"] )
        try:
            data = s.loads( token )
        except:
            return False

        if data.get( "confirm" ) != self.pk:
            return False

        self.confirmed = True
        db.session.add( self ) # @UndefinedVariable
        return True


    def GenerateResetToken( self, expiration=3600 ):
        s = Serializer( current_app.config["SECRET_KEY"], expiration )
        return s.dumps( {"reset": self.pk} )


    def ResetPassword( self, token, new_password ):
        s = Serializer( current_app.config["SECRET_KEY"] )
        try:
            data = s.loads( token )
        except:
            return False

        if data.get( "reset" ) != self.pk:
            return False

        self.password = new_password
        db.session.add( self ) # @UndefinedVariable
        return True


    def GenerateEmailChangeToken( self, new_email, expiration=3600 ):
        s = Serializer( current_app.config["SECRET_KEY"], expiration )
        return s.dumps( {"change_email": self.pk, "new_email": new_email} )


    def ChangeEmail( self, token ):
        s = Serializer( current_app.config["SECRET_KEY"] )
        try:
            data = s.loads( token )
        except:
            return False

        if data.get( "change_email" ) != self.pk:
            return False

        new_email = data.get( "new_email" )
        if new_email is None:
            return False
        if self.query.filter_by( email=new_email ).first() is not None:
            return False

        self.email = new_email
        self.avatar_hash = hashlib.md5( self.email.encode( "utf-8" ) ).hexdigest()
        db.session.add( self ) # @UndefinedVariable
        return True


    def Can( self, permissions ):
        return self.role is not None and ( self.role.permissions & permissions ) == permissions


    def Ping( self ):
        self.last_seen = datetime.utcnow()
        db.session.add( self ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable


    def Gravatar( self, size=100, default="monsterid", rating="g" ):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"

        hassh = self.avatar_hash or hashlib.md5( self.email.encode( "utf-8" ) ).hexdigest()
        return "{url}/{hassh}?s={size}&d={default}&r={rating}".format( 
            url=url,
            hassh=hassh,
            size=size,
            default=default,
            rating=rating
        )


    def is_administer( self ):
        return self.Can( DdPermission.ADMINISTER )


    def get_id( self ):
        return self.pk


    def __repr__( self ):
        return "<User %r>" % self.username


    @staticmethod
    def GenerateTestingUsers():
        """
        Generates users for testing purposes.
        """
        user = DdUser()
        user.username = "turtle"
        user.email = "foo@bar.com"
        user.password = "ninja"
        user.confirmed = True

        user1 = DdUser()
        user1.username = "montreal"
        user1.email = "foo1@bar.com"
        user1.password = "qazzaq"
        user1.confirmed = True

        db.session.add_all( [user, user1] ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable


class DdAnonymousUser( AnonymousUserMixin ):
    def Can( self, permissions ): # @UnusedVariable
        return False

    def is_administer( self ):
        return False


class DdDaoUser( object ):
    """
    Data Access Object for DdUser model.
    """

    def FindUserByPartOfUsername( self, search_token="" ):
        st = "%" + search_token + "%"
        return DdUser.query.filter( DdUser.username.like( st ) ).all()

    def GetAllFriendsForUser( self, user_pk=0 ):
        return DdUser.query.from_statement( 
            text( FRIENDS_SQL ).params( 
                user_pk=user_pk
            )
        ).all()

    def GetNumberOfFriends( self, user_pk=0 ):
        query_res = db.engine.execute( # @UndefinedVariable
            text( NUMBER_OF_FRIENDS_SQL ).params( 
                user_pk=user_pk
            )
        ).first()
        return query_res["number_of_friends"]

    def GetNumberOfUsers( self ):
        return DdUser.query.count()

    def GetUserByUsername( self, username="" ):
        return DdUser.query.filter_by( username=username ).first()
