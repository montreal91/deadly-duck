
import json
from collections import namedtuple

from sqlalchemy import and_

from app import db
from app.custom_queries import CURRENT_MATCH_SQL, DAY_RESULTS_SQL
from app.custom_queries import STANDINGS_SQL, STANDINGS_FOR_DIVISION_SQL

class DdMatchStatuses:
    planned = "planned"
    finished = "finished"
    aborted = "aborted"

DdMatchSnapshot = namedtuple( 
    "DdMathcSnapshot",
    [
        "pk",
        "home_team",
        "home_team_pk",
        "away_team",
        "away_team_pk",
        "home_player",
        "away_player",
        "home_skill",
        "away_skill",
        "full_score"
    ],
    rename=True
 )

DdStandingsRowSnapshot = namedtuple( 
    "DdStandingsRowSnapshot",
    [
        "club_pk",
        "club_name",
        "played_matches",
        "sets_won",
        "games_won"
    ],
    rename=True
 )

class DdMatch( db.Model ):
    __tablename__ = "matches"
    match_pk_n = db.Column( db.Integer, primary_key=True, index=True ) # @UndefinedVariable
    home_team_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ), index=True ) # @UndefinedVariable
    away_team_pk = db.Column( db.Integer, db.ForeignKey( "clubs.club_id_n" ), index=True ) # @UndefinedVariable
    user_pk = db.Column( db.Integer, db.ForeignKey( "users.pk" ), index=True ) # @UndefinedVariable
    home_player_pk = db.Column( db.Integer, db.ForeignKey( "players.pk_n" ), nullable=True, index=True ) # @UndefinedVariable
    away_player_pk = db.Column( db.Integer, db.ForeignKey( "players.pk_n" ), nullable=True, index=True ) # @UndefinedVariable
    season_n = db.Column( db.Integer, default=0, index=True ) # @UndefinedVariable
    day_n = db.Column( db.Integer, default=0, index=True ) # @UndefinedVariable
    context_json = db.Column( db.Text ) # @UndefinedVariable
    status_en = db.Column( # @UndefinedVariable
        db.Enum( # @UndefinedVariable
            DdMatchStatuses.planned,
            DdMatchStatuses.finished,
            DdMatchStatuses.aborted
        ),
        nullable=False,
        default=DdMatchStatuses.planned,
        index=True
    )

    playoff_series_pk = db.Column( db.Integer, db.ForeignKey( "playoff_series.pk" ) ) # @UndefinedVariable

    home_sets_n = db.Column( db.Integer, default=0 ) # @UndefinedVariable
    away_sets_n = db.Column( db.Integer, default=0 ) # @UndefinedVariable
    home_games_n = db.Column( db.Integer, default=0 ) # @UndefinedVariable
    away_games_n = db.Column( db.Integer, default=0 ) # @UndefinedVariable
    full_score_c = db.Column( db.String( 128 ), default="" ) # @UndefinedVariable

    home_club = db.relationship( "DdClub", foreign_keys=[home_team_pk] ) # @UndefinedVariable
    away_club = db.relationship( "DdClub", foreign_keys=[away_team_pk] ) # @UndefinedVariable
    home_player = db.relationship( "DdPlayer", foreign_keys=[home_player_pk] ) # @UndefinedVariable
    away_player = db.relationship( "DdPlayer", foreign_keys=[away_player_pk] ) # @UndefinedVariable

    @property
    def context( self ):
        return json.loads( self.context_json )

    @context.setter
    def context( self, value ):
        self.context_json = str( json.dumps( value ) )

    def SetAbortedStatus( self ):
        self.status_en = DdMatchStatuses.aborted

    def SetFinishedStatus( self ):
        self.status_en = DdMatchStatuses.finished

    def SetPlannedStatus( self ):
        self.status_en = DdMatchStatuses.planned

    def __repr__( self ):
        return "<Match #{0:d} {1:d} vs {2:d}>".format( 
            self.match_pk_n,
            self.home_team_pk,
            self.away_team_pk
        )

class DdDaoMatch( object ):
    def CreateNewMatch( 
        self,
        user_pk=0,
        season=0,
        day=0,
        home_team_pk=0,
        away_team_pk=0,
    ):
        match = DdMatch()
        match.home_team_pk = home_team_pk
        match.away_team_pk = away_team_pk
        match.user_pk = user_pk
        match.season_n = season
        match.day_n = day
        context = {}
        context["home_club"] = None
        context["away_club"] = None
        context["home_player_name"] = None
        context["away_player_name"] = None
        context["home_skill"] = None
        context["away_skill"] = None
        match.context = context
        match.playoff_series_pk = None
        match.SetPlannedStatus()
        return match

    def CreateNewMatchForSeries( self, series=None, day=0, top_home=True ):
        match = DdMatch()
        if top_home:
            match.home_team_pk = series.top_seed_pk
            match.away_team_pk = series.low_seed_pk
        else:
            match.home_team_pk = series.low_seed_pk
            match.away_team_pk = series.top_seed_pk
        match.user_pk = series.user_pk
        match.season_n = series.season_n
        match.day_n = day
        match.playoff_series_pk = series.pk
        match.SetPlannedStatus()
        return match

    def GetCurrentMatch( self, user ):
        match = db.engine.execute( # @UndefinedVariable
            CURRENT_MATCH_SQL.format( 
                user.managed_club_pk,
                user.current_season_n,
                user.current_day_n,
                user.pk
            )
        ).first() # @UndefinedVariable
        if match:
            return DdMatchSnapshot( 
                pk=match[0],
                home_team=match[1],
                away_team=match[2],
                home_player=None,
                away_player=None,
                home_skill=None,
                away_skill=None,
                full_score="",
                home_team_pk=match[3],
                away_team_pk=match[4]
            )
        else:
            return None

    def GetDivisionStandings( self, user_pk=0, season=0, division=0 ):
        table = db.engine.execute( # @UndefinedVariable
            STANDINGS_FOR_DIVISION_SQL.format( # @UndefinedVariable
                season,
                user_pk,
                division
            )
        ).fetchall() # @UndefinedVariable
        return [
            DdStandingsRowSnapshot( 
                club_pk=row[0],
                club_name=row[1],
                played_matches=row[4],
                sets_won=row[2],
                games_won=row[3]
            )
            for row in table
        ]

    def GetLeagueStandings( self, user_pk=0, season=0 ):
        table = db.engine.execute( # @UndefinedVariable
            STANDINGS_SQL.format( 
                season,
                user_pk
            )
        ).fetchall() # @UndefinedVariable
        return [
            DdStandingsRowSnapshot( 
                club_pk=row[0],
                club_name=row[1],
                played_matches=row[4],
                sets_won=row[2],
                games_won=row[3]
            )
            for row in table
        ]

    def GetRecentStandings( self, user, for_draft=False ):
        table = db.engine.execute( # @UndefinedVariable
            STANDINGS_SQL.format( 
                user.current_season_n - int( for_draft ),
                user.pk
            )
        ).fetchall() # @UndefinedVariable
        return [row[0] for row in reversed( table )]

    def GetDayResults( self, user_pk, season, day ):
        query_res = db.engine.execute( DAY_RESULTS_SQL.format( user_pk, season, day ) ).fetchall() # @UndefinedVariable
        return [
            DdMatchSnapshot( 
                pk=row[0],
                home_team=row[1],
                away_team=row[2],
                home_player=row[3],
                away_player=row[4],
                home_skill=round( row[5], 2 ),
                away_skill=round( row[6], 2 ),
                full_score=row[7],
                home_team_pk=row["home_team_pk"],
                away_team_pk=row["away_team_pk"]
            )
            for row in query_res
        ]

    def GetNumberOfFinishedMatches( self ):
        return DdMatch.query.filter_by( status_en=DdMatchStatuses.finished ).count()

    def GetTodayMatches( self, user ):
        return DdMatch.query.filter( 
            and_( 
                DdMatch.season_n == user.current_season_n,
                DdMatch.day_n == user.current_day_n,
                DdMatch.user_pk == user.pk,
                DdMatch.status_en == DdMatchStatuses.planned
            )
        ).all()

    def SaveMatch( self, match=None ):
        db.session.add( match ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable

    def SaveMatches( self, matches=[] ):
        db.session.add_all( matches ) # @UndefinedVariable
        db.session.commit() # @UndefinedVariable
