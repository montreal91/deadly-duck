
from json               import loads

from flask              import abort
from flask              import flash
from flask              import jsonify
from flask              import redirect
from flask              import render_template
from flask              import request
from flask              import url_for
from flask_login        import current_user
from flask_login        import login_required

from app                import db
from app.data.main.role import DdRole
from app.data.main.user import DdUser
from app.data.models    import DdPost
from app.decorators     import AdminRequired
from app.main           import main
from app.main.forms     import DdEditProfileAdminForm
from app.main.forms     import DdEditProfileForm
from app.main.forms     import DdMakeFriendRequestForm
from app.main.forms     import DdWriteMessageForm
from app.main.forms     import DdUserSearchForm

from config_game        import DdMiscConstants


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


@main.route( "/add_education/" )
@login_required
def AddEducation():
    universities = main.service.GetAllUniversities()
    return render_template( 
        "main/add_education.html",
        universities=universities
    )


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


@main.route( "/edit_education/" )
@login_required
def EditEducation():
    universities = main.service.GetAllUniversities()
    return render_template( 
        "main/edit_education.html",
        universities=universities
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
        number_of_users=number_of_users,
        max_users=DdMiscConstants.MAX_USERS.value,
        version=DdMiscConstants.CURRENT_VERSION.value
    )

@main.route( "/messages/" )
@login_required
def Messages():
    incoming_messages = main.service.GetAllIncomingMessages( user_pk=current_user.pk )
    outcoming_messages = main.service.GetAllOutcomingMessages( user_pk=current_user.pk )
    return render_template( 
        "main/messages.html",
        incoming_messages=incoming_messages,
        outcoming_messages=outcoming_messages
    )

@main.route( "/message/<int:pk>/" )
@login_required
def ReadMessage( pk ):
    message = main.service.GetMessageByPk( pk )
    if message.from_pk != current_user.pk and message.to_pk != current_user.pk:
        abort( 403 )
    if not message.is_read and message.to_pk == current_user.pk:
        message.is_read = True
        main.service.SaveMessage( message=message )
    return render_template( "main/full_message.html", message=message )

@main.route( "/reject_friend_request/<int:pk>/" )
@login_required
def RejectFriendRequest( pk ):
    request = main.service.GetFriendRequestByPk( request_pk=pk )
    if request.to_pk != current_user.pk:
        abort( 403 )

    request.is_rejected = True
    main.service.SaveFriendRequest( friend_request=request )
    return redirect( url_for( "main.Friends" ) )

@main.route( "/remove_education/<int:faculty_pk>/" )
@login_required
def RemoveEducation( faculty_pk ):
    main.service.RemoveEducationFromUser( user=current_user, faculty_pk=faculty_pk )
    return redirect( url_for( "main.User", username=current_user.username ) )

@main.route( "/remove_from_friends/<int:pk>/" )
@login_required
def RemoveFromFriends( pk ):
    friendshp_object = main.service.GetFriendshipObject( u1_pk=current_user.pk, u2_pk=pk )
    friendshp_object.is_active = False
    main.service.SaveFriendship( friendship_object=friendshp_object )
    return redirect( url_for( "main.Friends" ) )


@main.route( "/_submit_add_education/", methods=["POST"] )
@login_required
def SubmitAddEducation():
    data = loads( request.form["values"] )
    main.service.AddNewEducation( 
        user=current_user,
        university_pk=int( data["university_pk"] ),
        faculty_pk=int( data["faculty_pk"] )
    )
    return jsonify( res="New education is successfully added. Now you can add new education." )


@main.route( "/_university_faculties/", methods=["POST"] )
@login_required
def UniversityFaculties():
    university_pk = request.form["university_pk"]
    faculties = main.service.GetUniversityFaculties( university_pk )
    response = render_template( "includes/faculties.html", faculties=faculties )
    return jsonify( res=response )


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
    is_messaging_possible = main.service.IsMessagingPossible( 
        user1_pk=current_user.pk,
        user2_pk=user.pk
    )
    classmates = main.service.GetClassmatesForUser( user=user )
    return render_template( 
        "user.html",
        user=user,
        posts=posts,
        best_user_record=best_user_record,
        is_friendship_possible=is_friendship_possible,
        is_messaging_possible=is_messaging_possible,
        classmates=classmates
    )

@main.route( "/user_search/", methods=["GET", "POST"] )
@login_required
def UserSearch():
    form = DdUserSearchForm()
    search_results = []
    if form.validate_on_submit():
        search_token = form.username.data
        search_results = main.service.FindUserByPartOfUsername( search_token=search_token )
    return render_template( 
        "main/user_search.html",
        form=form,
        search_results=search_results
    )

@main.route( "/write_message/<username>/", methods=["GET", "POST"] )
@login_required
def WriteMessageToUser( username ):
    user = main.service.GetUserByUsername( username=username )
    if user is None:
        return abort( 404 )
    form = DdWriteMessageForm()
    if form.validate_on_submit():
        message = main.service.CreateMessage( 
            from_pk=current_user.pk,
            to_pk=user.pk,
            subject=form.subject.data,
            text=form.message.data
        )
        main.service.SaveMessage( message=message )
        return redirect( url_for( "main.Messages" ) )
    return render_template( "main/write_message.html", user=user, form=form )
