
from flask              import render_template, redirect, request
from flask              import url_for, flash
from flask.ext.login    import login_required, current_user

from .                  import game
from ..                 import db
from ..models           import DdUser, DdClub
from config_game        import club_names


@game.route( "/start-new-career/" )
@login_required
def StartNewCareer():
    if current_user.managed_club_pk is None:
        divisions = []
        for div in club_names:
            res = DdClub.query.filter_by( division_n=div )
            divisions.append( res.all() )
        return render_template( "game/start_new_career.html", divisions=divisions )
    else:
        return redirect(url_for("main.Index"))


@game.route( "/start-new-career/<pk>/" )
@login_required
def ChooseManagedClub( pk ):
    if current_user.managed_club_pk is None:
        current_user.managed_club_pk = pk
        db.session.add( current_user )
        db.session.commit()

        return redirect( url_for( "game.MainScreen" ) )
    else:
        return redirect( url_for( "main.Index" ) )


@game.route( "/main/" )
@login_required
def MainScreen():
    if current_user.managed_club_pk is not None:
        club = DdClub.query.get( current_user.managed_club_pk )

        return render_template( "game/main_screen.html", club=club )
    else:
        return redirect( url_for( "main.Index" ) )
