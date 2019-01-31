
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user

from app import db
from app.auth import auth
from app.auth.oauth import DdOAuthSignIn


@auth.route("/login/", methods=["GET", "POST"])
def Login():
    if current_user.is_authenticated:
        return redirect(url_for("main.Index"))
    return render_template("auth/login.html")


@auth.route("/logout/")
@login_required
def Logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.Index"))


@auth.route("/authorize/<provider>/")
def OauthAuthorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for("main.Index"))
    oauth = DdOAuthSignIn.GetProvider(provider)
    return oauth.Authorize()


@auth.route("/callback/<provider>/")
def OauthCallback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for("main.Index"))

    oauth = DdOAuthSignIn.GetProvider(provider)
    social_pk, username, email = oauth.Callback()

    if social_pk is None:
        flash("Authentication failed.")
        return redirect(url_for("main.Index"))

    user = auth.main_service.GetUserBySocialPk(social_pk)

    if not user:
        user = auth.main_service.CreateNewUser(
            social_pk=social_pk,
            username=username,
            email=email,
        )
    login_user(user)
    return redirect(url_for("main.Index"))
