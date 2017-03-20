
#!/usr/bin/env python

import os

from app                import CreateApp, db
from app.data.models    import DdPost
from app.data.game.club import DdClub
from app.data.game.club_record import DdClubRecord
from app.data.game.game_service import DdGameService
from app.data.game.match import DdMatch
from app.data.game.player import DdPlayer
from app.data.game.playoff_series import DdPlayoffSeries
from app.data.main.role import DdRole, DdPermission
from app.data.main.user import DdUser
from flask_migrate  import Migrate, MigrateCommand
from flask_script   import Manager, Shell


app = CreateApp( os.getenv( "FLASK_CONFIG" ) or "default" )
manager = Manager( app )
migrate = Migrate( app, db )

def ConfirmUser( username=None, email=None ):
    u = None
    if username:
        u = DdUser.query.filter_by( username=username ).first() # @UndefinedVariable
    elif email:
        u = DdUser.query.filter_by( email=email ).first() # @UndefinedVariable
    else:
        print( "You should specify username or email" )
        return

    if u is None:
        print( "No such user in the database." )
        return

    u.confirmed = True
    db.session.add( u ) # @UndefinedVariable
    db.session.commit() # @UndefinedVariable


def MakeShellContext():
    return dict( 
        app=app,
        db=db,
        DdClub=DdClub,
        DdClubRecord=DdClubRecord,
        DdMatch=DdMatch,
        DdPermission=DdPermission,
        DdPlayer=DdPlayer,
        DdPlayoffSeries=DdPlayoffSeries,
        DdPost=DdPost,
        DdRole=DdRole,
        DdUser=DdUser,
        ConfirmUser=ConfirmUser
    )

manager.add_command( "shell", Shell( make_context=MakeShellContext ) )
manager.add_command( "db", MigrateCommand )


@manager.command
def test():
    import unittest
    tests = unittest.TestLoader().discover( "tests" )
    unittest.TextTestRunner( verbosity=2 ).run( tests )

@manager.command
def initapp():
    service = DdGameService()
    DdUser.GenerateTestingUsers()
    service.InsertClubs()

if __name__ == '__main__':
    manager.run()
