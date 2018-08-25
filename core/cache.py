"""
Created on Jun 21, 2017

@author: montreal91
"""

from functools              import wraps

from werkzeug.contrib.cache import MemcachedCache


class DdCache( object ):
    def __init__( self, flask_app=None ):
        self.app = flask_app
        self._cache = None

        if flask_app is not None:
            servers = self.app.config["MEMCACHED_SERVERS"]
            timeout = self.app.config["MEMCACHED_DEFAULT_TIMEOUT"]
            self._cache = MemcachedCache( servers )
            self._cache.default_timeout = timeout

    def init_app( self, app ):
        self.app = app
        servers = self.app.config["MEMCACHED_SERVERS"]
        timeout = self.app.config["MEMCACHED_DEFAULT_TIMEOUT"]
        self._cache = MemcachedCache( servers )
        self._cache.default_timeout = timeout


    def Cached( self, timeout=5 * 60, key="" ):
        def decorator( f ):
            @wraps( f )
            def decorated_function( *args, **kwargs ):
                cache_key = key.format( **kwargs )
                rv = self._cache.get( cache_key )
                if rv is not None:
                    return rv
                rv = f( *args, **kwargs )
                self._cache.set( cache_key, rv, timeout=timeout )
                return rv
            return decorated_function
        return decorator

    def Get( self, key ):
        return self._cache.get( key )

    def DeleteKey( self, key ):
        self._cache.delete( key )

    def SetKey( self, key="", value=None ):
        self._cache.set( key, value )
