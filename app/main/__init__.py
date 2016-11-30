
# Blueprint creation

from flask      import Blueprint


main = Blueprint( "main", __name__ )

from .                  import views, errors
from app.data.models    import DdPermission


@main.app_context_processor
def InjectPermissions():
    return dict( Permissions=DdPermission )
