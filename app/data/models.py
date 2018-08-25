
from datetime                   import datetime

from app                        import db
from app                        import login_manager
from app.custom_queries         import MAX_DAY_IN_SEASON_SQL
from app.data.main.education    import DdFaculty
from app.data.main.education    import DdUniversity
from app.data.main.friendship   import DdFriendRequest
from app.data.main.friendship   import DdFriendship
from app.data.main.message      import DdMessage
from app.data.main.user         import DdUser
from app.data.main.user         import DdAnonymousUser


login_manager.anonymous_user = DdAnonymousUser


@login_manager.user_loader
def load_user( user_id ):
    user = DdUser.query.get( int( user_id ) )
    if user is None:
        return user
    max_day = db.engine.execute( MAX_DAY_IN_SEASON_SQL.format( user.pk, user.current_season_n ) ).first() # @UndefinedVariable
    user.season_last_day = max_day[0]
    return user


class DdPost( db.Model ):
    __tablename__ = "posts"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    body = db.Column( db.Text ) # @UndefinedVariable
    timestamp = db.Column( db.DateTime, index=True, default=datetime.utcnow ) # @UndefinedVariable
    author_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable
