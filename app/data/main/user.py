
import hashlib

from datetime           import datetime

from flask              import current_app
from flask              import request
from flask_login        import AnonymousUserMixin
from flask_login        import UserMixin
from itsdangerous       import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy         import text

from app                import db
from app.custom_queries import FRIENDS_SQL
from app.custom_queries import NUMBER_OF_FRIENDS_SQL
from app.data.main.role import DdPermission
from app.data.main.role import DdRole


class DdUser( UserMixin, db.Model ):
    __tablename__ = "users"
    pk = db.Column( db.Integer, primary_key=True )
    username = db.Column( db.String( 64 ), index=True )
    social_pk = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column( db.String( 64 ), index=True )
    role_pk = db.Column( db.Integer, db.ForeignKey( "roles.pk" ) )
    name = db.Column( db.String( 64 ) )
    location = db.Column( db.String( 64 ) )
    about_me = db.Column( db.Text() )
    member_since = db.Column( db.DateTime(), default=datetime.utcnow )
    last_seen = db.Column( db.DateTime(), default=datetime.utcnow )
    avatar_hash = db.Column( db.String( 32 ) )
    posts = db.relationship( "DdPost", backref="author", lazy="dynamic" )

    managed_club_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ) )
    current_season_n = db.Column( db.Integer, default=1 )
    current_day_n = db.Column( db.Integer, default=0 )


    def __init__( self, **kwargs ):
        super( DdUser, self ).__init__( **kwargs )
        if self.role is None:
            if self.email == current_app.config["FLASKY_ADMIN"]:
                self.role = DdRole.query.filter_by( permissions=0xff ).first()
            if self.role is None:
                self.role = DdRole.query.filter_by( default=True ).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5( 
                    self.email.encode( "utf-8" )
                ).hexdigest()


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
        db.session.add( self )
        return True


    def Can( self, permissions ):
        perm_condition = ( self.role.permissions & permissions ) == permissions
        return self.role is not None and perm_condition


    def Ping( self ):
        self.last_seen = datetime.utcnow()
        db.session.add( self )
        db.session.commit()


    def Gravatar( self, size=100, default="monsterid", rating="g" ):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"

        hassh = None
        if self.avatar_hash:
            hassh = self.avatar_hash
        elif self.email:
            hassh = hashlib.md5( self.email.encode( "utf-8" ) ).hexdigest()
        else:
            hassh = hashlib.md5( self.social_pk.encode( "utf-8" ) ).hexdigest()

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


class DdAnonymousUser( AnonymousUserMixin ):
    def Can( self, permissions ):
        return False

    def is_administer( self ):
        return False


class DdDaoUser( object ):
    """
    Data Access Object for DdUser model.
    """
    def CreateNewUser( self, social_pk, username, email ) -> DdUser:
        user = DdUser( social_pk=social_pk, username=username, email=email )
        db.session.add( user )
        db.session.commit()
        return user

    def FindUserByPartOfUsername( self, search_token="" ) -> list:
        st = "%" + search_token + "%"
        return DdUser.query.filter( DdUser.username.like( st ) ).all()


    def GetAllFriendsForUser( self, user_pk: int = 0 ) -> list:
        return DdUser.query.from_statement( 
            text( FRIENDS_SQL ).params( 
                user_pk=user_pk
            )
        ).all()


    def GetNumberOfFriends( self, user_pk=0 ):
        query_res = db.engine.execute(
            text( NUMBER_OF_FRIENDS_SQL ).params( 
                user_pk=user_pk
            )
        ).first()
        return query_res["number_of_friends"]


    def GetNumberOfUsers( self ) -> int:
        return DdUser.query.count()


    def GetUserBySocialPk( self, social_pk: str ) -> DdUser:
        return DdUser.query.filter_by( social_pk=social_pk ).first()


    def GetUserByUsername( self, username: str = "" ) -> DdUser:
        return DdUser.query.filter_by( username=username ).first()
