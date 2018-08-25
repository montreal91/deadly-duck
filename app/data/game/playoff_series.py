
from flask                      import url_for
from sqlalchemy                 import and_
from sqlalchemy                 import text

from app                        import db
from app.custom_queries         import FINAL_PLAYOFF_SERIES_FOR_CLUB_SQL
from app.custom_queries         import MAX_PLAYOFF_ROUND_SQL
from app.custom_queries         import PLAYOFF_SERIES_SQL
from app.custom_queries         import SERIES_IN_ONE_ROUND_IN_ONE_DIVISION_SQL
from configuration.config_game  import DdLeagueConfig


class DdPlayoffSeriesStatuses:
    PLANNED = 0
    IN_PROGRESS = 1
    FINISHED = 2


class DdPlayoffSeries( db.Model ):
    __tablename__ = "playoff_series"
    pk = db.Column( db.Integer, primary_key=True, index=True )
    top_seed_pk = db.Column( db.ForeignKey( "clubs.club_id_n" ), index=True )
    low_seed_pk = db.Column( db.ForeignKey( "clubs.club_id_n" ), index=True )
    user_pk = db.Column( db.ForeignKey( "users.pk" ), index=True )

    top_seed_victories_n = db.Column( db.Integer, default=0, nullable=False )
    low_seed_victories_n = db.Column( db.Integer, default=0, nullable=False )

    season_n = db.Column( db.Integer, default=0, nullable=False, index=True )
    round_n = db.Column( db.Integer, default=0, nullable=False, index=True )
    is_finished = db.Column( db.Boolean, default=False, nullable=False )

    matches = db.relationship( "DdMatch", backref="playoff_series" )

    top_seed = db.relationship( "DdClub", foreign_keys=[top_seed_pk] )
    low_seed = db.relationship( "DdClub", foreign_keys=[low_seed_pk] )

    @property
    def dictionary( self ):
        top_seed = {
            "club_name": self.top_seed.club_name_c,
            "matches": self.top_seed_victories_n,
        }

        low_seed = {
            "club_name": self.low_seed.club_name_c,
            "matches": self.low_seed_victories_n,
        }
        return {
            "top_seed": top_seed,
            "low_seed": low_seed,
            "pk": self.pk,
            "url": url_for("game.PlayoffSeriesDetails", series_pk=self.pk)
        }

    def GetLowSeedMatchesWon( self, sets_to_win=0 ):
        return sum( self._GetSetsLowSpeedWon( m ) == sets_to_win for m in self.matches )

    def GetLooserPk( self, sets_to_win=0, matches_to_win=0 ):
        top = self.GetTopSeedMatchesWon( sets_to_win=sets_to_win )
        low = self.GetLowSeedMatchesWon( sets_to_win=sets_to_win )

        if top >= matches_to_win:
            return self.low_seed_pk
        elif low >= matches_to_win:
            return self.top_seed_pk
        else:
            return None

    def GetTopSeedMatchesWon( self, sets_to_win=0 ):
        return sum( self._GetSetsTopSpeedWon( m ) == sets_to_win for m in self.matches )

    def GetWinnerPk( self, sets_to_win=0, matches_to_win=0 ):
        top = self.GetTopSeedMatchesWon( sets_to_win=sets_to_win )
        low = self.GetLowSeedMatchesWon( sets_to_win=sets_to_win )

        if top == matches_to_win:
            return self.top_seed_pk
        elif low == matches_to_win:
            return self.low_seed_pk
        else:
            return None

    def IsFinished( self, matches_to_win=0 ):
        condition1 = self.top_seed_victories_n == matches_to_win
        condition2 = self.low_seed_victories_n == matches_to_win
        if condition1 or condition2:
            return True
        else:
            return False

    def _GetSetsLowSpeedWon( self, match ):
        if match.home_team_pk == self.low_seed_pk:
            return match.home_sets_n
        elif match.away_team_pk == self.low_seed_pk:
            return match.away_sets_n
        else:
            raise ValueError( "Low seed had not played this match." )

    def _GetSetsTopSpeedWon( self, match ):
        if match.home_team_pk == self.top_seed_pk:
            return match.home_sets_n
        elif match.away_team_pk == self.top_seed_pk:
            return match.away_sets_n
        else:
            raise ValueError( "Top seed had not played this match." )

    def __repr__( self ):
        return "<DdPlayoffSeries #{0:d} {1:d} vs {2:d} season #{3:d}>".format( 
            self.pk,
            self.top_seed_pk,
            self.low_seed_pk,
            self.season_n
        )

class DdDaoPlayoffSeries( object ):
    def CreatePlayoffSeries( self, top_seed_pk=0, low_seed_pk=0, round_n=0, user=None ):
        """
        Creates new playoff series.
        Does not save it in the db.
        Returns created series.
        """
        series = DdPlayoffSeries()
        series.user_pk = user.pk
        series.season_n = user.current_season_n
        series.top_seed_pk = top_seed_pk
        series.low_seed_pk = low_seed_pk
        series.round_n = round_n
        return series

    def GetAllPlayoffSeries( self, user_pk, season ):
        return DdPlayoffSeries.query.from_statement( 
            text( PLAYOFF_SERIES_SQL ).params(
                userpk=user_pk,
                season=season
            )
        ).all()

    def GetFinalPlayoffSeriesForClubInSeason( self, club_pk=0, user=None ):
        return DdPlayoffSeries.query.from_statement( 
            text( FINAL_PLAYOFF_SERIES_FOR_CLUB_SQL ).params( 
                userpk=user.pk,
                season=user.current_season_n,
                club_pk=club_pk,
            )
        ).first()


    def GetMaxPlayoffRound( self, user=None ):
        res = db.engine.execute(
            MAX_PLAYOFF_ROUND_SQL.format( 
                user_pk=user.pk,
                season=user.current_season_n
            )
        ).first()
        return res["max_round"]

    def GetNumberOfFinishedSeries( self ):
        return DdPlayoffSeries.query.filter_by( is_finished=True ).count()

    def GetPlayoffSeries( self, series_pk=0 ):
        return DdPlayoffSeries.query.get_or_404( series_pk )

    def GetPlayoffSeriesByRoundAndDivision( self, user=None, rnd=0 ):
        div1 = DdPlayoffSeries.query.from_statement( 
            text( SERIES_IN_ONE_ROUND_IN_ONE_DIVISION_SQL ).params( 
                user=user.pk,
                season=user.current_season_n,
                division=1,
                rnd=rnd
            )
        ).all()
        div2 = DdPlayoffSeries.query.from_statement( 
            text( SERIES_IN_ONE_ROUND_IN_ONE_DIVISION_SQL ).params( 
                user=user.pk,
                season=user.current_season_n,
                division=2,
                rnd=rnd
            )
        ).all()
        return div1, div2

    def SavePlayoffSeries( self, pos=None ):
        pos.is_finished = pos.IsFinished( 
            matches_to_win=DdLeagueConfig.MATCHES_TO_WIN,
        )
        db.session.add( pos )
        db.session.commit()

    def SavePlayoffSeriesList( self, series_list=[] ):
        for srs in series_list:
            srs.is_finished = srs.IsFinished( 
                matches_to_win=DdLeagueConfig.MATCHES_TO_WIN,
            )
        db.session.add_all( series_list )
        db.session.commit()
