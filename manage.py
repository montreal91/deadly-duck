
#!/usr/bin/env python

import os

from app                import CreateApp, db
from app.models         import DdPlayer
from app.models         import DdPost, DdClub, DdMatch
from app.models         import DdUser, DdRole, DdPermission
from flask.ext.migrate  import Migrate, MigrateCommand
from flask.ext.script   import Manager, Shell


app = CreateApp( os.getenv( "FLASK_CONFIG" ) or "default" )
manager = Manager( app )
migrate = Migrate( app, db )

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
    DdUser.GenerateTestingUser()
    DdClub.InsertClubs()

if __name__ == '__main__':
    manager.run()
