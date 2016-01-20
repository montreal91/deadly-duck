
from flask  import render_template

from .      import main


@main.app_errorhandler( 403 )
def Forbidden( e ):
    return render_template( "403.html" ), 403


@main.app_errorhandler( 404 )
def PageNotFound( e ):
    return render_template( "404.html" ), 404


@main.app_errorhandler( 500 )
def InternalServerError( e ):
    return render_template( "500.html" ), 500
