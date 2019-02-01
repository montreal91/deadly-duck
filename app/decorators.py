
from functools import wraps

from flask import abort
from flask_login import current_user

from app.data.main.role import DdPermission


def PermissionRequired(permission):
    def decorator(fun):
        @wraps(fun)
        def decorated_function(*args, **kwargs):
            if not current_user.Can(permission):
                abort(403)
            return fun(*args, **kwargs)
        return decorated_function
    return decorator


def AdminRequired(fun):
    return PermissionRequired(DdPermission.ADMINISTER)(fun)
