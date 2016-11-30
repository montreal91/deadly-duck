
from flask import abort
from sqlalchemy import and_

from app import db

class DdClubFinancialAccount( db.Model ):
    __tablename__ = "financial_accounts"
    pk_n = db.Column( db.Integer, primary_key=True )
    user_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) )
    club_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ) )
    money_nn = db.Column( db.Numeric( 10, 2 ), nullable=False, default=0.0 )

    @property
    def money( self ):
        return self.money_nn

class DdDaoClubFinancialAccount( object ):
    def AddFunds( self, user_pk=0, club_pk=0, funds=0 ):
        """Be careful. Funds can be negative"""
        account = self.GetFinancialAccount( user_pk, club_pk )
        account.money_nn += funds
        self.SaveAccount( account )


    def GetFinancialAccount( self, user_pk=0, club_pk=0 ):
        account = DdClubFinancialAccount.query.filter(
            and_(
                DdClubFinancialAccount.user_pk == int( user_pk ),
                DdClubFinancialAccount.club_pk == int( club_pk )
            )
        ).first()
        if account:
            return account
        else:
            abort( 404 )

    def SaveAccount( self, account ):
        db.session.add( account )
        db.session.commit()

    def SaveAccounts( self, accounts=[] ):
        db.session.add_all( accounts )
        db.session.commit()
