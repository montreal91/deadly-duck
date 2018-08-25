
from app import db

faculty_registrations = db.Table( # @UndefinedVariable
    "faculty_registrations",
    db.Column( "user_pk", db.Integer, db.ForeignKey( "users.pk" ) ), # @UndefinedVariable
    db.Column( "faculty_pk", db.Integer, db.ForeignKey( "faculties.pk" ) ) # @UndefinedVariable
 )

university_registrations = db.Table( # @UndefinedVariable
    "university_registrations",
    db.Column( "user_pk", db.Integer, db.ForeignKey( "users.pk" ) ), # @UndefinedVariable
    db.Column( "university_pk", db.Integer, db.ForeignKey( "universities.pk" ) ) # @UndefinedVariable
 )


class DdFaculty( db.Model ):
    __tablename__ = "faculties"
    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    name_c = db.Column( db.String( 64 ), nullable=False, index=True ) # @UndefinedVariable
    university_pk = db.Column( db.Integer, db.ForeignKey( "universities.pk" ) ) # @UndefinedVariable

    university = db.relationship( "DdUniversity", backref="faculties" ) # @UndefinedVariable
    students = db.relationship( # @UndefinedVariable
        "DdUser",
        secondary=faculty_registrations,
        backref=db.backref( "faculties", lazy="dynamic" ), # @UndefinedVariable
        lazy="dynamic"
    )

    def __repr__( self ):
        return "<DdFaculty {name:s} in {university:s}>".format( 
            name=self.name_c,
            university=self.university.name_c
        )


class DdUniversity( db.Model ):
    __tablename__ = "universities"

    pk = db.Column( db.Integer, primary_key=True ) # @UndefinedVariable
    name_c = db.Column( db.String( 64 ), unique=True, nullable=False, index=True ) # @UndefinedVariable

    students = db.relationship( # @UndefinedVariable
        "DdUser",
        secondary=university_registrations,
        backref=db.backref( "universities", lazy="dynamic" ), # @UndefinedVariable
        lazy="dynamic"
    )

    def __repr__( self ):
        return "<" + str( self.pk ) + " " + self.name_c + ">"


class DdDaoFaculty( object ):
    def AddUserToFaculty( self, faculty=None, user=None ):
        faculty.students.append( user )
        self.SaveFaculty( faculty )

    def Create( self, name="", university_pk=0 ):
        faculty = DdFaculty()
        faculty.name_c = name
        faculty.university_pk = university_pk
        return faculty

    def GetFacultiesByUniversity( self, university_pk=0 ):
        return DdFaculty.query.filter_by( university_pk=university_pk ).all()

    def GetFacultyByPk( self, pk=0 ):
        return DdFaculty.query.get( pk )

    def RemoveUserFromFaculty( self, faculty=None, user=None ):
        faculty.students.remove( user )
        self.SaveFaculty( faculty )

    def SaveFaculty( self, faculty=None ):
        db.session.add( faculty ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable


class DdDaoUniversity( object ):
    def AddUserToUniversity( self, university=None, user=None ):
        university.students.append( user )
        self.SaveUniversity( university )

    def Create( self, name="" ):
        university = DdUniversity()
        university.name_c = name
        return university

    def GetAllUniversities( self ):
        return DdUniversity.query.all()

    def GetUniversityByPk( self, pk=0 ):
        return DdUniversity.query.get( pk )

    def RemoveUserFromUniversity( self, university=None, user=None ):
        university.students.remove( user )
        self.SaveUniversity( university )

    def SaveUniversity( self, university=None ):
        db.session.add( university ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable
