
# Application package constructor

from flask                  import Flask
from flask.ext.bootstrap    import Bootstrap
from flask.ext.login        import LoginManager
from flask.ext.mail         import Mail
from flask.ext.moment       import Moment
from flask.ext.sqlalchemy   import SQLAlchemy

from config                 import config


bootstrap       = Bootstrap()
mail            = Mail()
moment          = Moment()
db              = SQLAlchemy()
login_manager   = LoginManager()

login_manager.session_protection    = "strong"
login_manager.login_view            = "auth.Login"


def CreateApp( config_name ):
    app = Flask( __name__ )
    app.config.from_object( config[ config_name ] )
    config[ config_name ].InitApp( app )

    bootstrap.init_app( app )
    mail.init_app( app )
    moment.init_app( app )
    db.init_app( app )
    login_manager.init_app( app )

    # Blueprints registration
    from .main import main as main_blueprint
    app.register_blueprint( main_blueprint )

    from .auth import auth as auth_blueprint
    app.register_blueprint( auth_blueprint, url_prefix="/auth" )

    return app
