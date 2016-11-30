
#!/usr/bin/env python

import os

from app                import CreateApp, db
from app.data.models    import DdPost
from app.data.models    import DdUser, DdRole, DdPermission
from app.data.game.club import DdClub
from app.data.game.match import DdMatch
from app.data.game.player import DdPlayer
from app.data.game.game_service import DdGameService
from flask.ext.migrate  import Migrate, MigrateCommand
from flask.ext.script   import Manager, Shell


app = CreateApp( os.getenv( "FLASK_CONFIG" ) or "default" )
manager = Manager( app )
migrate = Migrate( app, db )

def ConfirmUser( username=None, email=None ):
    u = None
    if username:
        u = DdUser.query.filter_by( username=username ).first()
    elif email:
        u = DdUser.query.filter_by( email=email ).first()
    else:
        print( "You should specify username or email" )
        return

    if u is None:
        print( "No such user in the database." )
        return

    u.confirmed = True
    db.session.add( u )
    db.session.commit()


def MakeShellContext():
    return dict( 
        app=app,
        db=db,
        DdClub=DdClub,
        DdMatch=DdMatch,
        DdPermission=DdPermission,
        DdPlayer=DdPlayer,
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
    DdUser.GenerateTestingUser()
    service.InsertClubs()

if __name__ == '__main__':
    manager.run()
