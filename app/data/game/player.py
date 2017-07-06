
import json
import math
from decimal                import Decimal
from random                 import randint

from sqlalchemy             import and_
from sqlalchemy             import text

from app                    import db
from app.custom_queries     import RECENT_PLAYER_MATCHES_SQL
from app.custom_queries     import NEWCOMERS_SQL
from app.data.game.match    import DdMatchSnapshot
from config_game            import number_of_recent_matches
from config_game            import retirement_age
from config_game            import DdPlayerSkills


class DdPlayer( db.Model ):
    __tablename__ = "players"
    pk_n = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    first_name_c = db.Column( db.String( 64 ), nullable=False ) # @UndefinedVariable
    second_name_c = db.Column( db.String( 64 ) ) # @UndefinedVariable
    last_name_c = db.Column( db.String( 64 ), nullable=False ) # @UndefinedVariable

    current_stamina_n = db.Column( db.Numeric( 5, 2 ), default=100.0 ) # @UndefinedVariable
    age_n = db.Column( db.Integer, default=20 ) # @UndefinedVariable
    is_active = db.Column( db.Boolean, default=True ) # @UndefinedVariable
    is_drafted = db.Column( db.Boolean, default=False ) # @UndefinedVariable

    user_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ) ) # @UndefinedVariable
    club_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ) ) # @UndefinedVariable

    endurance_pk = db.Column( db.Integer, db.ForeignKey( "skills.pk" ) ) # @UndefinedVariable
    technique_pk = db.Column( db.Integer, db.ForeignKey( "skills.pk" ) ) # @UndefinedVariable

    user = db.relationship( "DdUser", foreign_keys=[user_pk] ) # @UndefinedVariable
    club = db.relationship( "DdClub", foreign_keys=[club_pk] ) # @UndefinedVariable
    endurance = db.relationship( # @UndefinedVariable
        "DdSkillModel",
        foreign_keys=[endurance_pk],
        lazy="subquery"
    )
    technique = db.relationship( # @UndefinedVariable
        "DdSkillModel",
        foreign_keys=[technique_pk],
        lazy="subquery"
    )

    @property
    def actual_technique( self ):
        stamina_factor = int( self.current_stamina_n ) / self.max_stamina
        return round( self.technique.current_maximum_n * stamina_factor )

    @property
    def match_salary( self ):
        return DdPlayer.CalculateSalary( 
            skill=self.technique.current_maximum_n,
            age=self.age_n
        )

    @property
    def max_stamina( self ):
        return self.endurance.current_maximum_n * DdPlayerSkills.ENDURANCE_FACTOR

    @property
    def passive_salary( self ):
        res = DdPlayer.CalculateSalary( 
            skill=self.technique.current_maximum_n,
            age=self.age_n
        )
        return round( res / 2, 2 )

    @property
    def full_name( self ):
        return self.first_name_c + " " + self.second_name_c + " " + self.last_name_c


    def AgeUp( self ):
        self.age_n += 1
        if self.age_n >= retirement_age:
            self.is_active = False

    def RecoverStamina( self, recovered_stamina=0 ):
        self.current_stamina_n += recovered_stamina
        if self.current_stamina_n > self.max_stamina:
            self.current_stamina_n = self.max_stamina


    def RemoveStaminaLostInMatch( self, lost_stamina=0 ):
        self.current_stamina_n -= Decimal( lost_stamina )
        if self.current_stamina_n < 0:
            self.current_stamina_n = Decimal( 0 )

    def AddEnduranceExperience( self, experience ):
        self.endurance.AddExperience( experience )

    def AddTechniqueExperience( self, experience ):
        self.technique.AddExperience( experience )

    @staticmethod
    def GetNames():
        with open( "names.json" ) as datafile:
            all_names = json.load( datafile )
        return all_names["names"], all_names["surnames"]

    @staticmethod
    def CalculateMatchEnduranceExperience( stamina ):
        return int( round( 0.8 * stamina ** 2 ) )

    @staticmethod
    def CalculateMatchTechniqueExperience( games_lost=0, games_won=0, sets_lost=0, sets_won=0 ):
        game_exp = games_lost + games_won ** 2
        set_exp = sets_lost * DdPlayerSkills.SET_EXPERIENCE_FACTOR / 5
        set_exp += sets_won * DdPlayerSkills.SET_EXPERIENCE_FACTOR
        return game_exp + set_exp

    @staticmethod
    def CalculateSalary( skill=0, age=0 ):
        return round( Decimal( skill * 10 ) - Decimal( math.exp( age - retirement_age ) ) + 100, 2 )

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
    def CreatePlayer( self, first_name="", second_name="", last_name="", user_pk=0, endurance=None, technique=None ):
        player = DdPlayer()
        player.first_name_c = first_name
        player.second_name_c = second_name
        player.last_name_c = last_name
        player.user_pk = user_pk
        player.endurance = endurance
        player.technique = technique
        player.current_stamina_n = endurance.current_maximum_n
        player.age_n = randint( 17, 20 )
        return player

    def GetAllActivePlayers( self, user_pk=0 ):
        return DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_active == True
            )
        ).all()

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        qres = DdPlayer.query.options( 
            db.joinedload( DdPlayer.endurance ), # @UndefinedVariable
            db.joinedload( DdPlayer.technique ) # @UndefinedVariable
        )
        qres = qres.filter( and_( 
            DdPlayer.club_pk == club_pk,
            DdPlayer.user_pk == user_pk,
            DdPlayer.is_active == True,
        ) )
        return qres.all()

    def GetFreeAgents( self, user_pk ):
        res = DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user_pk,
                DdPlayer.club_pk == None,
                DdPlayer.is_active == True,
                DdPlayer.is_drafted == True
            )
        )
        return res.all()

    # TODO: rename this method to 'GetNewcomersForUser
    def GetNewcomersSnapshotsForUser( self, user_pk: int ) -> list:
        query_res = DdPlayer.query.from_statement( 
            text( NEWCOMERS_SQL ).params( 
                userpk=user_pk,
            )
        ).all()
        return query_res

    def GetNumberOfActivePlayers( self ):
        return DdPlayer.query.filter_by( is_active=True ).count()

    def GetNumberOfUndraftedPlayers( self, user_pk: int ) -> int:
        return DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_drafted == False
            )
        ).count()

    def GetPlayer( self, player_pk ):
        qres = DdPlayer.query.options( 
            db.joinedload( DdPlayer.technique ), # @UndefinedVariable
            db.joinedload( DdPlayer.endurance ) # @UndefinedVariable
        )
        return qres.get( player_pk )

    def GetPlayerRecentMatches( self, player_pk, season ):
        query_res = db.engine.execute( # @UndefinedVariable
            RECENT_PLAYER_MATCHES_SQL.format( 
                player_pk,
                season,
                number_of_recent_matches
            )
        ).fetchall() # @UndefinedVariable
        return [
            DdMatchSnapshot( 
                pk=res[0],
                home_team=res[1],
                away_team=res[2],
                home_player=res[3],
                away_player=res[4],
                home_skill=None,
                away_skill=None,
                full_score=res[5],
                home_team_pk=None,
                away_team_pk=None
            ) for res in query_res
        ]

    def SavePlayer( self, player ):
        db.session.add( player ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SavePlayers( self, players=[] ):
        db.session.add_all( players ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SaveRosters( self, rosters={} ):
        players = []
        for club_pk in rosters:
            for plr in rosters[club_pk]:
                player = DdPlayer.query.get( plr.pk )
                player.club_pk = club_pk
                player.is_drafted = True
                players.append( player )
        db.session.add_all( players ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

def PlayerModelComparator( player_model ):
    res = player_model.actual_technique + player_model.technique.absolute_maximum_n
    res += player_model.endurance.current_maximum_n + player_model.endurance.absolute_maximum_n
    res += player_model.current_stamina_n * Decimal( 1.5 )
    return res
