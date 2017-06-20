
import json
import math
from decimal                import Decimal
from random                 import randint

from sqlalchemy             import and_, text

from app                    import db
from app.custom_queries     import RECENT_PLAYER_MATCHES_SQL, CLUB_PLAYERS_SQL
from app.custom_queries     import NEWCOMERS_SQL
from app.data.game.match    import DdMatchSnapshot
from config_game            import number_of_recent_matches, retirement_age
from config_game            import DdPlayerSkills

class DdPlayerSnapshot( object ):
    def __init__( 
        self,
        pk=0,
        technique=0,
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
        self._technique = Decimal( technique )
        self._current_stamina = int( current_stamina )
        self._endurance = endurance
        self._first_name = first_name
        self._last_name = last_name
        self._second_name = second_name
        self._age = age
        self._club_pk = club_pk
        self._match_salary = match_salary
        self._passive_salary = passive_salary

        self._new_endurance_experience = 0
        self._new_technique_experience = 0

    @property
    def pk( self ):
        return self._pk

    @property
    def technique( self ):
        return round( self._technique, DdPlayerSkills.SKILL_PRECISION )

    @property
    def actual_technique( self ):
        stamina_factor = Decimal( self._current_stamina ) / Decimal( self.max_stamina )
        return round( self._technique * stamina_factor, DdPlayerSkills.SKILL_PRECISION )

    @property
    def current_stamina( self ):
        return round( self._current_stamina, DdPlayerSkills.SKILL_PRECISION )

    @property
    def max_stamina( self ):
        return self._endurance * DdPlayerSkills.ENDURANCE_FACTOR

    @property
    def endurance( self ):
        return round( self._endurance, DdPlayerSkills.SKILL_PRECISION )

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
    def new_endurance_experience( self ):
        return self._new_endurance_experience

    @property
    def new_technique_experience( self ):
        return self._new_technique_experience

    @property
    def passive_salary( self ):
        return self._passive_salary


    @staticmethod
    def CalculateMatchTechniqueExperience( games_lost=0, games_won=0, sets_lost=0, sets_won=0 ):
        game_exp = games_lost + games_won ** 2
        set_exp = sets_lost * DdPlayerSkills.SET_EXPERIENCE_FACTOR / 5
        set_exp += sets_won * DdPlayerSkills.SET_EXPERIENCE_FACTOR
        return game_exp + set_exp

    @staticmethod
    def CreateSnapshotFromModel( player ):
        snapshot = DdPlayerSnapshot()
        snapshot._pk = player.pk_n
        snapshot._first_name = player.first_name_c
        snapshot._second_name = player.second_name_c
        snapshot._last_name = player.last_name_c
        snapshot._age = player.age_n
        snapshot._current_stamina = int( round( player.current_stamina_n ) )
        snapshot._technique = player.technique.current_maximum_n
        snapshot._endurance = player.endurance.current_maximum_n
        snapshot._match_salary = player.match_salary
        snapshot._passive_salary = player.passive_salary
        snapshot._club_pk = player.club_pk
        return snapshot


    def AddEnduranceExperience( self, experience ):
        self._new_endurance_experience += int( round( 0.8 * experience ** 2 ) )

    def AddTechniqueExperience( self, experience ):
        self._new_technique_experience += experience


    def DropNewEnduranceExperience( self ):
        self._new_endurance_experience = 0

    def DropNewTechniqueExperience( self ):
        self._new_technique_experience = 0

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
        backref="player"
    )
    technique = db.relationship( # @UndefinedVariable
        "DdSkillModel",
        foreign_keys=[technique_pk]
    )

    @property
    def match_salary( self ):
        return DdPlayer.CalculateSalary( 
            skill=self.technique.current_maximum_n,
            age=self.age_n
        )

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

    @property
    def snapshot( self ):
        return DdPlayerSnapshot.CreateSnapshotFromModel( self )

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
        self.endurance.AddExperience( snapshot.new_endurance_experience )
        self.technique.AddExperience( snapshot.new_technique_experience )
        snapshot.DropNewEnduranceExperience()
        snapshot.DropNewTechniqueExperience()

    @staticmethod
    def GetNames():
        with open( "names.json" ) as datafile:
            all_names = json.load( datafile )
        return all_names["names"], all_names["surnames"]

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

    def GetAllActivePlayers( self, user_pk ):
        return DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_active == True
            )
        ).all()

    def GetClubPlayers( self, user_pk=0, club_pk=0 ):
        query_res = DdPlayer.query.from_statement( 
            text( CLUB_PLAYERS_SQL ).params( 
                userpk=user_pk,
                clubpk=club_pk
            )
        ).all()
        return [player.snapshot for player in query_res]

    def GetFreeAgents( self, user_pk ):
        res = DdPlayer.query.filter( 
            and_( 
                DdPlayer.user_pk == user_pk,
                DdPlayer.club_pk == None,
                DdPlayer.is_active == True,
                DdPlayer.is_drafted == True
            )
        )
        return [player.snapshot for player in res]

    def GetNewcomersSnapshotsForUser( self, user ):
        query_res = DdPlayer.query.from_statement( 
            text( NEWCOMERS_SQL ).params( 
                userpk=user.pk,
            )
        ).all()
        return [plr.snapshot for plr in query_res]

    def GetNumberOfActivePlayers( self ):
        return DdPlayer.query.filter_by( is_active=True ).count()

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
