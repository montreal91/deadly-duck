
from app                import db

class DdPermission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class DdRole( db.Model ):
    __tablename__ = "roles"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    name = db.Column( db.String( 64 ), unique=True ) # @UndefinedVariable
    default = db.Column( db.Boolean, default=False, index=True ) # @UndefinedVariable
    permissions = db.Column( db.Integer ) # @UndefinedVariable
    users = db.relationship( "DdUser", backref="role", lazy="dynamic" ) # @UndefinedVariable


    @staticmethod
    def InsertRoles():
        roles = {
            "User": ( 
                DdPermission.FOLLOW |
                DdPermission.COMMENT |
                DdPermission.WRITE_ARTICLES,
                True,
            ),
            "Moderator": ( 
                DdPermission.FOLLOW |
                DdPermission.COMMENT |
                DdPermission.WRITE_ARTICLES |
                DdPermission.MODERATE_COMMENTS,
                False,
            ),
            "Administrator": ( 0xff, False ),
        }

        for r in roles:
            role = DdRole.query.filter_by( name=r ).first()
            if role is None:
                role = DdRole( name=r )
            role.permissions = roles[ r ][ 0 ]
            role.default = roles[ r ][ 1 ]
            db.session.add( role )
        db.session.commit()

    def __repr__( self ):
        return "<Role %r>" % self.name

