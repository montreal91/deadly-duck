
import time
from datetime   import datetime
from unittest   import TestCase

from app        import CreateApp, db
from app.models import XUser, XRole, XAnonymousUser
from app.models import XPermission


class XUserModelTestCase( TestCase ):
    def setUp( self ):
        self.app            = CreateApp( "testing" )
        self.app_context    = self.app.app_context()
        self.app_context.push()
        db.create_all()
        XRole.InsertRoles()


    def tearDown( self ):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_password_setter( self ):
        u = XUser( password="cat" )
        self.assertTrue( u.password_hash is not None )


    def test_no_password_getter( self ):
        u = XUser( password="dog" )
        with self.assertRaises( AttributeError ):
            u.password


    def test_password_verification( self ):
        u = XUser( password="fox" )
        self.assertTrue( u.VerifyPassword( "fox" ) )
        self.assertFalse( u.VerifyPassword( "cat" ) )


    def test_password_salts_are_random( self ):
        u1 = XUser( password="cat" )
        u2 = XUser( password="fox" )
        self.assertTrue( u1.password_hash != u2.password_hash )


    def test_valid_confirmation_token( self ):
        u = XUser( password="cat" )
        db.session.add(u)
        db.session.commit()
        token = u.GenerateConfirmationToken()
        self.assertTrue( u.Confirm( token ) )


    def test_invalid_reset_token( self ):
        u1 = XUser( password="cat" )
        u2 = XUser( password="dog" )
        db.session.add( u1 )
        db.session.add( u2 )
        token = u1.GenerateResetToken()

        self.assertFalse( u2.ResetPassword( token, "horse" ) )
        self.assertTrue( u2.VerifyPassword( "dog" ) )


    def test_valid_email_change_token( self ):
        u = XUser( email="om@discworld.com", password="Turtle" )
        db.session.add( u )
        db.session.commit()
        token = u.GenerateEmailChangeToken( "great.god.om@discworld.com" )

        self.assertTrue( u.ChangeEmail( token ) )
        self.assertTrue( u.email == "great.god.om@discworld.com" )


    def test_invalid_email_change_token( self ):
        u1 = XUser( email="om@discworld.com", password="Turtle" )
        u2 = XUser( email="bruta@discworld.com", password="Horns" )
        db.session.add( u1 )
        db.session.add( u2 )
        db.session.commit()
        token = u1.GenerateEmailChangeToken( "vorbis@discworld.net" )

        self.assertFalse( u2.ChangeEmail( token ) )
        self.assertTrue( u2.email == "bruta@discworld.com" )


    def test_duplicate_email_change_token( self ):
        u1 = XUser( email="om@discworld.com", password="Turtle" )
        u2 = XUser( email="bruta@discworld.com", password="Horns" )
        db.session.add( u1 )
        db.session.add( u2 )
        db.session.commit()
        token = u2.GenerateEmailChangeToken( "om@discworld.com" )

        self.assertFalse( u2.ChangeEmail( token ) )
        self.assertTrue( u2.email == "bruta@discworld.com" )


    def test_roles_and_permissions( self ):
        u = XUser( email="om@discworld.com", password="Turtle" )

        self.assertTrue( u.Can( XPermission.WRITE_ARTICLES ) )
        self.assertFalse( u.Can( XPermission.MODERATE_COMMENTS ) )


    def test_anonymous_user( self ):
        u = XAnonymousUser()
        self.assertFalse( u.Can( XPermission.FOLLOW ) )

    def test_timestamps( self ):
        u = XUser( password="Turtle" )
        db.session.add( u )
        db.session.commit()

        self.assertTrue(
            ( datetime.utcnow() - u.member_since ).total_seconds() < 3
        )
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3
        )


    def test_ping( self ):
        u = XUser( password="Turtle" )
        db.session.add( u )
        db.session.commit()
        last_seen_before = u.last_seen
        time.sleep( 2 )
        u.Ping()

        self.assertTrue( u.last_seen > last_seen_before )
