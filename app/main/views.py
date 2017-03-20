
from flask              import render_template, redirect, url_for
from flask              import abort, flash
from flask_login        import login_required, current_user

from .                  import main
from .forms             import DdEditProfileForm, DdEditProfileAdminForm
from app.main.forms     import DdMakeFriendRequestForm
from ..                 import db
from ..decorators       import AdminRequired
from app.data.main.role import DdRole
from app.data.main.user import DdUser
from app.data.models    import DdPost


@main.route( "/accept_friend_request/<int:pk>/" )
@login_required
def AcceptFriendRequest( pk ):
    request = main.service.GetFriendRequestByPk( request_pk=pk )
    if request.to_pk != current_user.pk:
        abort( 403 )

    status = main.service.AcceptFriendRequest( request=request )
    if status is False:
        flash( "Such frienship is not possible." )
    else:
        request.is_accepted = True
        main.service.SaveFriendRequest( friend_request=request )
    return redirect( url_for( "main.Friends" ) )


@main.route( "/add_to_fiends/<username>/", methods=["GET", "POST"] )
@login_required
def AddToFriends( username ):
    user = main.service.GetUserByUsername( username=username )
    form = DdMakeFriendRequestForm()
    if form.validate_on_submit():
        status = main.service.MakeFriendRequest( 
            from_pk=current_user.pk,
            to_pk=user.pk,
            message=form.message.data
        )
        if status is False:
            flash( "Such friendship is already requested." )
        return redirect( url_for( "main.User", username=user.username ) )
    return render_template( "main/add_to_friends.html", user=user, form=form )


@main.route( "/cancel_friend_request/<int:pk>/" )
@login_required
def CancelFriendRequest( pk ):
    request = main.service.GetFriendRequestByPk( request_pk=pk )
    if request.from_pk != current_user.pk:
        abort( 403 )

    request.is_rejected = True
    main.service.SaveFriendRequest( friend_request=request )
    return redirect( url_for( "main.Friends" ) )


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


@main.route( "/friends/" )
@login_required
def Friends():
    friends = main.service.GetAllFriendsForUser( current_user.pk )
    incoming_requests = main.service.GetIncomingFriendRequests( user_pk=current_user.pk )
    outcoming_requests = main.service.GetOutcomingFriendRequests( user_pk=current_user.pk )
    return render_template( 
        "/main/friends.html",
        friends=friends,
        incoming_requests=incoming_requests,
        outcoming_requests=outcoming_requests
    )


@main.route( "/", methods=["GET", "POST"] )
def Index():
    ratings = main.game_service.GetGlobalRatings()
    number_of_active_players = main.game_service.GetNumberOfActivePlayers()
    number_of_finished_matches = main.game_service.GetNumberOfFinishedMatches()
    number_of_finished_series = main.game_service.GetNumberOfFinishedSeries()
    number_of_users = main.service.GetNumberOfUsers()
    return render_template( 
        "index.html",
        ratings=ratings,
        number_of_active_players=number_of_active_players,
        number_of_finished_matches=number_of_finished_matches,
        number_of_finished_series=number_of_finished_series,
        number_of_users=number_of_users
    )


@main.route( "/reject_friend_request/<int:pk>/" )
@login_required
def RejectFriendRequest( pk ):
    request = main.service.GetFriendRequestByPk( request_pk=pk )
    if request.to_pk != current_user.pk:
        abort( 403 )

    request.is_rejected = True
    main.service.SaveFriendRequest( friend_request=request )
    return redirect( url_for( "main.Friends" ) )

@main.route( "/remove_from_friends/<int:pk>/" )
@login_required
def RemoveFromFriends( pk ):
    friendshp_object = main.service.GetFriendshipObject( u1_pk=current_user.pk, u2_pk=pk )
    friendshp_object.is_active = False
    main.service.SaveFriendship( friendship_object=friendshp_object )
    return redirect( url_for( "main.Friends" ) )

@main.route( "/user/<username>/" )
@login_required
def User( username ):
    user = main.service.GetUserByUsername( username=username ) # @UndefinedVariable
    if user is None:
        return abort( 404 )
    posts = user.posts.order_by( DdPost.timestamp.desc() ).all() # @UndefinedVariable
    best_user_record = main.game_service.GetBestClubRecord( 
        user=user,
        club_pk=user.managed_club_pk
    )
    is_friendship_possible = main.service.IsFriendshipPossible( 
        user_one_pk=current_user.pk,
        user_two_pk=user.pk
    )
    return render_template( 
        "user.html",
        user=user,
        posts=posts,
        best_user_record=best_user_record,
        is_friendship_possible=is_friendship_possible
    )
