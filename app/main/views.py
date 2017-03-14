
from flask              import render_template, redirect, url_for
from flask              import abort, flash
from flask_login        import login_required, current_user

from .                  import main
from .forms             import DdEditProfileForm, DdEditProfileAdminForm, DdPostForm
from ..                 import db
from ..decorators       import AdminRequired
from app.data.game.game_service import DdGameService
from app.data.models    import DdUser, DdRole, DdPermission
from app.data.models    import DdPost


@main.route( "/", methods=["GET", "POST"] )
def Index():
    # form = DdPostForm()
    # if current_user.Can( DdPermission.WRITE_ARTICLES ) and form.validate_on_submit():
    #     post = DdPost()
    #     post.body = form.body.data
    #     post.author = current_user._get_current_object()

    #     db.session.add(post)
    #     db.session.commit()

    #     return redirect( url_for( ".Index" ) )
    # posts = DdPost.query.order_by( DdPost.timestamp.desc() ).all()
    ratings = main.game_service.GetGlobalRatings()
    return render_template( "index.html", ratings=ratings ) # , form=form, posts=posts, Permission=DdPermission )


@main.route( "/user/<username>/" )
@login_required
def User( username ):
    user = DdUser.query.filter_by( username=username ).first() # @UndefinedVariable
    if user is None:
        return abort( 404 )
    posts = user.posts.order_by( DdPost.timestamp.desc() ).all() # @UndefinedVariable
    best_user_record = main.game_service.GetBestClubRecord( user=user, club_pk=user.managed_club_pk )
    return render_template( 
        "user.html",
        user=user,
        posts=posts,
        best_user_record=best_user_record
    )


@main.route( "/edit-profile/", methods=["GET", "POST"] )
@login_required
def EditProfile():
    form = DdEditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data

        db.session.add( current_user ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

        flash( "Your profile has been updated." )
        return redirect( url_for( ".User", username=current_user.username ) )

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template( "edit_profile.html", form=form )


@main.route( "/edit-profile/<int:pk>/", methods=["GET", "POST"] )
@login_required
@AdminRequired
def EditProfileAdmin( pk ):
    user = DdUser.query.get_or_404( pk ) # @UndefinedVariable
    form = DdEditProfileAdminForm( user=user )
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = DdRole.query.get( form.role.data ) # @UndefinedVariable
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data

        db.session.add( user ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

        flash( "The profile has been updated." )
        return redirect( url_for( ".User", username=user.username ) )

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_pk
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template( "edit_profile.html", form=form, user=user )
