
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
from config_game        import DdPlayerSkills
from stat_tools         import GeneratePositiveIntegerGauss

class DdPlayerSnapshot( object ):
    def __init__( 
        self,
        pk=0,
        skill=0,
        current_stamina=0,
        endurance=0,
        first_name="",
        last_name="",
        second_name="",
        age=0,
        club_pk=0,
        match_salary=0,
        passive_salary=0
    ):
        super( DdPlayerSnapshot, self ).__init__()
        self._pk = pk
        self._skill = skill
        self._current_stamina = current_stamina
        self._endurance = endurance
        self._first_name = first_name
        self._last_name = last_name
        self._second_name = second_name
        self._age = age
        self._club_pk = club_pk
        self._match_salary = match_salary
        self._passive_salary = passive_salary

    @property
    def pk( self ):
        return self._pk

    @property
    def skill( self ):
        return self._skill

    @property
    def actual_skill( self ):
        stamina_factor = self._current_stamina / self.max_stamina
        return round( self._skill * stamina_factor, 2 )

    @property
    def current_stamina( self ):
        return self._current_stamina

    @property
    def max_stamina( self ):
        return self._endurance * DdPlayerSkills.ENDURANCE_FACTOR

    @property
    def endurance( self ):
        return self._endurance

    @property
    def first_name( self ):
        return self._first_name

    @property
    def last_name( self ):
        return self._last_name

    @property
    def second_name( self ):
        return self._second_name

    @property
    def age( self ):
        return self._age

    @property
    def club_pk( self ):
        return self._club_pk

    @property
    def match_salary( self ):
        return self._match_salary

    @property
    def passive_salary( self ):
        return self._passive_salary

    def RecoverStamina( self, recovered_stamina=0 ):
        self._current_stamina += recovered_stamina
        if self._current_stamina > self.max_stamina:
            self._current_stamina = self.max_stamina

    def RemoveStaminaLostInMatch( self, lost_stamina=0 ):
        self._current_stamina -= lost_stamina
        if self._current_stamina < 0:
            self._current_stamina = 0

    def __repr__( self ):
        return "<PlayerSnapshot #{0:d} {1}. {2}. {3}>".format( 
            self.pk,
            self.first_name[0],
            self.second_name[0],
            self.last_name
        )


class DdPlayer( db.Model ):
    __tablename__ = "players"
    pk_n = db.Column( db.Integer, primary_key=True )
    first_name_c = db.Column( db.String( 64 ), nullable=False )
    second_name_c = db.Column( db.String( 64 ) )
    last_name_c = db.Column( db.String( 64 ), nullable=False )

    skill_n = db.Column( db.Integer, nullable=False, default=5 )
    endurance_n = db.Column( db.Integer, default=10 )
    current_stamina_n = db.Column( db.Integer, default=100 )
    age_n = db.Column( db.Integer, default=20 )
    is_active = db.Column( db.Boolean, default=True )
    is_drafted = db.Column( db.Boolean, default=False )

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
            current_stamina=self.current_stamina_n,
            endurance=self.endurance_n,
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

    def UpdateBySnapshot( self, snapshot=DdPlayerSnapshot( endurance=1 ) ):
        """
        It just changes values in current object.
        To save changes in the database, according dao or service is required.
        """
        assert self.pk_n == snapshot.pk
        self.current_stamina_n = snapshot.current_stamina

    @staticmethod
    def GetNames():
        with open( "names.json" ) as datafile:
            all_names = json.load( datafile )
        return all_names["names"], all_names["surnames"]

    @staticmethod
    def CalculateSalary( skill=0, age=0 ):
        return round( skill * 10 - math.exp( age - retirement_age ) + 100, 2 )

    def __repr__( self ):
        return "<Player {0:d} {1}. {2}. {3}>".format( 
            self.pk_n,
            self.first_name_c[0],
            self.second_name_c[0],
            self.last_name_c
        )


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
                current_stamina=row[8],
                endurance=row[7],
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
    def GetNewcomersSnapshotsForUser( self, user ):
        players = DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user.pk,
#                 DdPlayer.club_pk == None,
                DdPlayer.is_drafted == False
            )
        ).order_by( DdPlayer.skill_n ).all()
        return [plr.snapshot for plr in players]

    def GetNumberOfUndraftedPlayers( self, user ):
        return DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user.pk,
                DdPlayer.is_drafted == False
            )
        ).count()

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
            player.skill_n = GeneratePositiveIntegerGauss( 
                DdPlayerSkills.MEAN_VALUE,
                DdPlayerSkills.STANDARD_DEVIATION,
                DdPlayerSkills.MAX_VALUE
            )
            player.endurance_n = GeneratePositiveIntegerGauss( 
                DdPlayerSkills.MEAN_VALUE,
                DdPlayerSkills.STANDARD_DEVIATION,
                DdPlayerSkills.MAX_VALUE
            )
            player.current_stamina_n = player.endurance_n * DdPlayerSkills.ENDURANCE_FACTOR
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
                player.is_drafted = True
                players.append( player )
        db.session.add_all( players )
        db.session.commit()
