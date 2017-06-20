
from random import choice, randint

from app import db
from config_game import DdPlayerSkills
from stat_tools import GeneratePositiveGauss

class DdSkillModel( db.Model ):
    __tablename__ = "skills"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    absolute_maximum_n = db.Column( db.SmallInteger, nullable=False ) # @UndefinedVariable
    current_maximum_n = db.Column( db.SmallInteger, nullable=False ) # @UndefinedVariable
    current_value_n = db.Column( db.SmallInteger, nullable=False ) # @UndefinedVariable
    talent_n = db.Column( db.SmallInteger, nullable=False ) # @UndefinedVariable
    experience_n = db.Column( db.Integer, nullable=False ) # @UndefinedVariable

    def AddExperience( self, value ):
        self.experience_n += value
        if self.experience_n >= self.ExperienceForSkillUp():
            self.current_maximum_n += 1
            self.experience_n = 0

        # Current maximum can't be any bigger than absolute maximum
        if self.current_maximum_n > self.absolute_maximum_n:
            self.current_maximum_n = self.absolute_maximum_n

    def ExperienceForSkillUp( self ):
        percent = round( self.current_maximum_n / self.absolute_maximum_n * 100 ) + 1
        return int( percent ** 2 / self.talent_n )


class DdDaoSkill( object ):
    """
    Data Access Object for DdSkillModel class.
    """
    def CreateSkill( self, absolute_maximum=0, current_maximum=0, talent=0 ):
        """
        Creates new DdSkillModel object.
        Does not save it in the database.
        :param absolute_maximum: positive integer less or equal than 100
        :param current_maximum: positive integer less or equal than 100
        :param talent: only can take values from app.data.game.DdSkillTalents enum.
        Returns created object
        """
        skill_model = DdSkillModel()
        skill_model.absolute_maximum_n = absolute_maximum
        skill_model.current_maximum_n = current_maximum
        skill_model.current_value_n = current_maximum
        skill_model.talent_n = talent
        skill_model.experience_n = 0
        return skill_model

    def GenerateNewSkill( self ):
        absmax = GeneratePositiveGauss( 
            a=DdPlayerSkills.MEAN_VALUE,
            sigma=DdPlayerSkills.STANDARD_DEVIATION,
            max_n=DdPlayerSkills.MAX_VALUE
        )
        absmax = int( round( absmax * 10 ) )
        if absmax < 15:
            absmax = 15
        curmax = int( round( absmax / randint( 2, 5 ) ) )
        talent = choice( DdPlayerSkills.POSSIBLE_TALENTS )
        return self.CreateSkill( 
            absolute_maximum=absmax,
            current_maximum=curmax,
            talent=talent
        )

    def SaveSkill( self, skill=None ):
        db.session.add( skill ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SaveSkills( self, skills=[] ):
        db.session.add_all( skills ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

