
import json
import math
from collections import namedtuple
from random             import choice, randint

from sqlalchemy import and_

from app import db
from app.custom_queries import RECENT_PLAYER_MATCHES_SQL, CLUB_PLAYERS_SQL
from app.data.game.match import DdMatchSnapshot
from app.data.game.club import DdClub
from config_game        import number_of_recent_matches, retirement_age


DdPlayerSnapshot = namedtuple( 
    "DdPlayerSnapshot",
    [
        "pk",
        "skill",
        "first_name",
        "last_name",
        "second_name",
        "age",
        "club_pk",
        "match_salary",
        "passive_salary",
    ],
    rename=True
 )

class DdPlayer( db.Model ):
    __tablename__ = "players"
    pk_n = db.Column( db.Integer, primary_key=True )
    first_name_c = db.Column( db.String( 64 ), nullable=False )
    second_name_c = db.Column( db.String( 64 ) )
    last_name_c = db.Column( db.String( 64 ), nullable=False )

    skill_n = db.Column( db.Integer, nullable=False, default=5 )
    age_n = db.Column( db.Integer, default=20 )
    is_active = db.Column( db.Boolean, default=True )

    user_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) )
    club_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ) )

    user = db.relationship( "DdUser", foreign_keys=[user_pk] )
    club = db.relationship( "DdClub", foreign_keys=[club_pk] )

    @property
    def match_salary( self ):
        return DdPlayer.CalculateSalary( skill=self.skill_n, age=self.age_n )

    @property
    def passive_salary( self ):
        res = DdPlayer.CalculateSalary( skill=self.skill_n, age=self.age_n ) / 2
        return round( res, 2 )

    @property
    def snapshot( self ):
        return DdPlayerSnapshot( 
            pk=self.pk_n,
            skill=self.skill_n,
            first_name=self.first_name_c,
            second_name=self.second_name_c,
            last_name=self.last_name_c,
            age=self.age_n,
            club_pk=self.club_pk,
            match_salary=self.match_salary,
            passive_salary=self.passive_salary
        )

    def AgeUp( self ):
        self.age_n += 1
        if self.age_n >= retirement_age:
            self.is_active = False

    def __repr__( self ):
        return "<Player {0:d} {1}. {2}. {3}>".format( 
            self.pk_n,
            self.first_name_c[0],
            self.second_name_c[0],
            self.last_name_c
        )

    @staticmethod
    def GetNames():
        with open( "names.json" ) as datafile:
            all_names = json.load( datafile )
        return all_names["names"], all_names["surnames"]

    @staticmethod
    def CalculateSalary( skill=0, age=0 ):
        return round( skill * 10 - math.exp( age - retirement_age ) + 100, 2 )


class DdDaoPlayer( object ):
    """
    Data Access Object for DdPlayer class
    """
    def GetAllActivePlayers( self, user_pk ):
        return DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_active == True
            )
        ).all()

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        query_res = db.engine.execute( CLUB_PLAYERS_SQL.format( user_pk, club_pk ) )
        return [
            DdPlayerSnapshot( 
                pk=row[0],
                first_name=row[1],
                second_name=row[2],
                last_name=row[3],
                skill=row[4],
                age=row[5],
                club_pk=club_pk,
                match_salary=DdPlayer.CalculateSalary( skill=row[4], age=row[5] ),
                passive_salary=round( DdPlayer.CalculateSalary( skill=row[4], age=row[5] ) / 2, 2 )
            ) for row in query_res
        ]

    def GetFreeAgents( self, user_pk ):
        res = DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user_pk,
                DdPlayer.club_pk == None
            )
        )
        return [player.snapshot for player in res]

    # TODO: rename this method to GetNewcomersSnapshots
    def GetNewcomersProxiesForUser( self, user ):
        players = DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user.pk,
                DdPlayer.club_pk == None,
                DdPlayer.age_n <= 20
            )
        ).order_by( DdPlayer.skill_n ).all()
        return [plr.snapshot for plr in players]

    def GetPlayer( self, player_pk ):
        return DdPlayer.query.get_or_404( player_pk )

    def GetPlayerRecentMatches( self, player_pk, season ):
        query_res = db.engine.execute( 
            RECENT_PLAYER_MATCHES_SQL.format( 
                player_pk,
                season,
                number_of_recent_matches
            )
        ).fetchall()
        return [
            DdMatchSnapshot( 
                pk=res[0],
                home_team=res[1],
                away_team=res[2],
                home_player=res[3],
                away_player=res[4],
                home_skill=None,
                away_skill=None,
                full_score=res[5]
            ) for res in query_res
        ]

    def CreateNewcomersForUser( self, user ):
        first_names, last_names = DdPlayer.GetNames()
        players = []
        for i in range( 24 ):
            player = DdPlayer()
            player.first_name_c = choice( first_names )
            player.second_name_c = choice( first_names )
            player.last_name_c = choice( last_names )
            player.skill_n = randint( 1, 10 )
            player.age_n = randint( 17, 20 )
            player.user_pk = user.pk
            players.append( player )
        db.session.add_all( players )
        db.session.commit()

    def CreatePlayersForUser( self, user ):
        first_names, last_names = DdPlayer.GetNames()
        clubs = DdClub.query.all()
        players = []
        for i in range( 4 ):
            for club in clubs:
                player = DdPlayer()
                player.first_name_c = choice( first_names )
                player.second_name_c = choice( first_names )
                player.last_name_c = choice( last_names )
                player.skill_n = randint( 1, 10 )
                player.age_n = randint( 18, 22 )
                player.user_pk = user.pk
                player.club_pk = club.club_id_n
                players.append( player )
        db.session.add_all( players )
        db.session.commit()

    def SavePlayer( self, player ):
        db.session.add( player )
        db.session.commit()

    def SavePlayers( self, players=[] ):
        db.session.add_all( players )
        db.session.commit()

    def SaveRosters( self, rosters={} ):
        players = []
        for club_pk in rosters:
            for plr in rosters[club_pk]:
                player = DdPlayer.query.get( plr.pk )
                player.club_pk = club_pk
                players.append( player )
        db.session.add_all( players )
        db.session.commit()
