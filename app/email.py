
import os
import smtplib

from threading      import Thread
from email.message  import EmailMessage

from flask          import current_app, render_template


def SendAsyncEmail( app, msg ):
    with app.app_context():
        mail.send( msg )


def SendEmail( to, subject, template, **kwargs ):
    app             = current_app._get_current_object()

    msg             = EmailMessage()
    msg["Subject"]  = subject
    msg["From"]     = os.environ.get( "MAIL_USERNAME" )
    msg["To"]       = to
    msg.set_content(render_template( template + ".txt", **kwargs ) )

    server          = smtplib.SMTP( app.config["MAIL_SERVER"], app.config["MAIL_PORT"] )
    server.starttls()
    server.ehlo()
    server.login( os.environ.get( "MAIL_USERNAME" ), os.environ.get( "MAIL_PASSWORD" ) )
    server.send_message( msg, os.environ.get( "MAIL_USERNAME", [to] ) )
    server.quit()
