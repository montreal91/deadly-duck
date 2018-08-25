
from flask              import flash
from flask              import redirect
from flask              import render_template
from flask              import request
from flask              import url_for
from flask_login        import current_user
from flask_login        import login_user
from flask_login        import login_required
from flask_login        import logout_user

from app                import db
from app.auth           import auth
from app.auth.forms     import DdChangeEmailForm
from app.auth.forms     import DdChangePasswordForm
from app.auth.forms     import DdLoginForm
from app.auth.forms     import DdPasswordResetForm
from app.auth.forms     import DdPasswordResetRequestForm
from app.auth.forms     import DdRegistrationForm
from app.data.models    import DdUser


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.Ping()
        if not current_user.confirmed and request.endpoint[:5] != "auth." \
            and request.endpoint != 'static':
            return redirect( url_for( "auth.Unconfirmed" ) )


@auth.route( "/unconfirmed/" )
def Unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect( url_for( "main.Index" ) )
    else:
        return render_template( "auth/unconfirmed.html" )


@auth.route( "/login/", methods=[ "GET", "POST" ] )
def Login():
    form = DdLoginForm()
    if form.validate_on_submit():
        user = DdUser.query.filter_by( email=form.email.data ).first()
        if user is not None and user.VerifyPassword( form.password.data ):
            login_user( user, form.remember_me.data )
            flash( "You have been logged in." )
            return redirect( request.args.get( "next" ) or url_for( "main.Index" ) )
        flash( "Invalid username or password." )
    return render_template( "auth/login.html", form=form )


@auth.route( "/logout/" )
@login_required
def Logout():
    logout_user()
    flash( "You have been logged out." )
    return redirect( url_for( "main.Index" ) )


@auth.route( "/register/", methods=[ "GET", "POST" ] )
def Register():
    form = DdRegistrationForm()
    if form.validate_on_submit():
        user = DdUser()
        user.email = form.email.data
        user.username = form.username.data
        user.password = form.password.data
        db.session.add( user )
        db.session.commit()
        flash( "A confirmation email has been sent to you by email." )
        return redirect( url_for( "auth.Login" ) )
    return render_template( "auth/register.html", form=form )


@auth.route( "/confirm/<token>/" )
@login_required
def Confirm( token ):
    if current_user.confirmed:
        return redirect( url_for( "main.Index" ) )
    if current_user.Confirm( token ):
        flash( "You have confirmed your account. Thanks!" )
    else:
        flash( "The confirmation link is invalid or has expired." )
    return redirect( url_for( "main.Index" ) )


@auth.route( "/confirm/" )
@login_required
def ResendConfirmation():
    token = current_user.GenerateConfirmationToken()
    SendEmail( 
        current_user.email,
        "Confirm Your Account",
        "auth/email/confirm",
        user=current_user,
        token=token
    )
    flash( "A new confirmation email has been sent to you by email." )
    return redirect( url_for( "main.Index" ) )


@auth.route( "/change-password/", methods=[ "GET", "POST" ] )
@login_required
def ChangePassword():
    form = DdChangePasswordForm()
    if form.validate_on_submit():
        if current_user.VerifyPassword( form.old_password.data ):
            current_user.password = form.password.data
            db.session.add( current_user )
            flash( "Your password has been updated." )
            return redirect( url_for( "main.Index" ) )
        else:
            flash( "Invalid password." )
    return render_template( "auth/change_password.html", form=form )


@auth.route( "/reset/", methods=[ "GET", "POST" ] )
def PasswordResetRequest():
    if not current_user.is_anonimous:
        return redirect( url_for( "main.Index" ) )

    form = DdPasswordResetRequestForm()
    if form.validate_on_submit():
        user = DdUser.query.filter_by( email=form.email.data ).first()
        if user:
            token = user.GenerateResetToken()
            SendEmail( 
                user.email,
                "Reset Your Password",
                "auth/email/reset_password",
                user=user,
                token=token,
                next=request.args.get( "next" )
            )
        flash( "An email with instructions to reset your password has been sent to you" )
        return redirect( url_for( "auth.Login" ) )
    return render_template( "auth/reset_password.html", form=form )


@auth.route( "/reset/<token>/", methods=[ "GET", "POST" ] )
def PasswordReset( token ):
    if not current_user.is_anonimous:
        return redirect( url_for( "main.Index" ) )

    form = DdPasswordResetForm()
    if form.validate_on_submit():
        user = DdUser.query.filter_by( email=form.email.data ).first()
        if user is None:
            return redirect( url_for( "main.Index" ) )

        if user.reset_password( token, form.password.data ):
            flash( "Your password has been updated." )
            return redirect( url_for( "auth.Login" ) )
        else:
            return redirect( url_for( "main.Index" ) )

    return render_template( "auth/reset_password.html", form=form )


@auth.route( "/change-email/", methods=[ "GET", "POST" ] )
@login_required
def ChangeEmailRequest():
    form = DdChangeEmailForm()
    if form.validate_on_submit():
        if current_user.VerifyPassword( form.password.data ):
            new_email = form.email.data
            token = current_user.GenerateEmailChangeToken( new_email )
            SendEmail( 
                new_email,
                "Confirm your email address",
                "auth/email/change_email",
                user=current_user,
                token=token
            )
            flash( 
                """An email with instructions to confirm your new email address
                has been sent to you."""
            )
            return redirect( url_for( "main.Index" ) )
        else:
            flash( "Invalid email or password." )
    return render_template( "auth/change_email.html", form=form )


@auth.route( "/change-email/<token>/", methods=[ "GET", "POST" ] )
@login_required
def ChangeEmail( token ):
    if current_user.ChangeEmail( token ):
        flash( "Your email address has been updated." )
    else:
        flash( "Invalid request." )

    return redirect( url_for( "main.Index" ) )
