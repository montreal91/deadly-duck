
from flask_wtf import Form
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import Required
from wtforms.validators import Regexp
from wtforms.validators import EqualTo

from app.data.models import DdUser


class DdLoginForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 64), Email()]
    )
    password = PasswordField("Password", validators=[Required()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class DdRegistrationForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 64), Email()]
    )
    username = StringField(
        "Userrname",
        validators=[
            Required(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, numbers, dots or underscores"
           )
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            Required(),
            EqualTo("password2", message="Passwords must match.")
        ]
    )
    password2 = PasswordField("Confirm password", validators=[Required()])
    submit = SubmitField("Register")


    def validate_email(self, field):
        if DdUser.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered")


    def validate_username(self, field):
        if DdUser.query.filter_by(username=field.data).first():
            raise ValidationError("Username is already in use.")


class DdChangePasswordForm(Form):
    old_password = PasswordField("Old password", validators=[Required()])
    password = PasswordField(
        "New password",
        validators=[
            Required(),
            EqualTo("password2", message="Passwords must match"),
        ]
   )
    password2 = PasswordField("Confirm new password", validators=[Required()])
    submit = SubmitField("Update Password")


class DdPasswordResetRequestForm(Form):
    email = StringField(
        "Email",
        validators=[
            Required(),
            Length(1, 64),
            Email()
        ]
   )
    submit = SubmitField("Reset Password")


class DdPasswordResetForm(Form):
    email = StringField(
        "Email",
        validators=[
            Required(),
            Length(1, 64),
            Email()
        ]
    )
    password = PasswordField(
        "New password",
        validators=[
            Required(),
            EqualTo("password2", message="Passwords must match"),
        ]
    )
    password2 = PasswordField("Confirm new password", validators=[Required()])
    submit = SubmitField("Reset Password")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError("Unknown email address.")


class DdChangeEmailForm(Form):
    email = StringField(
        "Email",
        validators=[
            Required(),
            Length(1, 64),
            Email()
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            Required(),
            EqualTo("password2", message="Passwords must match"),
        ]
    )
    submit = SubmitField("Update Email Address")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError("Email already registered.")
