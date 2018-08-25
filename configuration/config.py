
import json
import os

basedir = os.path.abspath( os.path.dirname( __file__ ) )

class DdConfig:
    FLASKY_MAIL_SUBJECT_PREFIX = "[Flasky]"
    FLASKY_MAIL_SENDER = "Flasky Admin <admin@flasky.com>"
    FLASKY_ADMIN = os.environ.get( "FLASKY_ADMIN" )
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get( "MAIL_USERNAME" )
    MAIL_PASSWORD = os.environ.get( "MAIL_PASSWORD" )
    MEMCACHED_DEFAULT_TIMEOUT = 10 * 60
    MEMCACHED_SERVERS = ["127.0.0.1:11211"]
    OAUTH_CREDENTIALS_FILE = "configuration/oauth_credentials_dev.json"
    SECRET_KEY = os.environ.get( "SECRET_KEY" ) or "go fork yourself"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


    @classmethod
    def GetOauthCredentials(cls) -> dict:
        credentials = {}

        with open(cls.OAUTH_CREDENTIALS_FILE) as credentials_file:
            credentials = json.load(credentials_file)
        return credentials


    @staticmethod
    def InitApp( app ) -> None:
        pass


class DdDevelopmentConfig( DdConfig ):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://duck:duck18@localhost/duck_dev"
    SQLALCHEMY_ECHO = True


class DdTestingConfig( DdConfig ):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get( "TEST_DATABASE_URL" ) or "sqlite:///" + os.path.join( basedir, "data-test.sqlite" )


class DdProductionConfig( DdConfig ):
    SQLALCHEMY_DATABASE_URI = os.environ.get( "DATABASE_URL" ) or "sqlite:///" + os.path.join( basedir, "data.sqlite" )


config = {
    "development": DdDevelopmentConfig,
    "testing": DdTestingConfig,
    "production": DdProductionConfig,
    "default": DdDevelopmentConfig,
}
