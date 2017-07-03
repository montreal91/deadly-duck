
from functools              import wraps

from flask                  import abort
from flask_login            import current_user

from app.data.main.role     import DdPermission


def PermissionRequired( permission ):
    def decorator( f ):
        @wraps( f )
        def decorated_function( *args, **kwargs ):
            if not current_user.Can( permission ):
                abort( 403 )
            return f( *args, **kwargs )
        return decorated_function
    return decorator


def AdminRequired( f ):
    return PermissionRequired( DdPermission.ADMINISTER )( f )
