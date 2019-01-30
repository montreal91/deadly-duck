
from datetime import datetime

from sqlalchemy import text

from app import db
from app.custom_queries import BEST_PLAYOFF_RECORD_SQL
from app.custom_queries import BEST_REGULAR_RECORD_SQL
from app.custom_queries import CLUB_RECORDS_SQL
from configuration.config_game import DdLeagueConfig


class DdClubRecord(db.Model):
    __tablename__ = "club_records"
    pk = db.Column(db.Integer, primary_key=True, index=True)
    club_pk = db.Column(
        db.Integer, db.ForeignKey("clubs.club_id_n"), index=True
    )
    user_pk = db.Column(db.Integer, db.ForeignKey("users.pk"), index=True)
    season_n = db.Column(db.Integer, index=True)

    regular_season_position_n = db.Column(db.Integer, default=0)
    regular_season_points_n = db.Column(db.Integer, default=0)
    last_playoff_series_pk = db.Column(
        db.Integer, db.ForeignKey("playoff_series.pk")
    )
    last_playoff_series = db.relationship(
        "DdPlayoffSeries",
        foreign_keys=[last_playoff_series_pk]
    )

    timestamp_dt = db.Column(db.DateTime(), default=datetime.utcnow)

class DdDaoClubRecord(object):
    def CreateClubRecord(
        self,
        club_pk=0,
        user=None,
        position=0,
        points=0,
        playoff_series=None,
        is_winner=False
    ):
        record = DdClubRecord()
        record.club_pk = club_pk
        record.user_pk = user.pk
        record.season_n = user.current_season_n
        record.regular_season_position_n = position
        record.regular_season_points_n = points
        if playoff_series is not None:
            record.last_playoff_series_pk = playoff_series.pk
        else:
            record.last_playoff_series_pk = None
        record.is_winner = is_winner

        return record

    def GetPlayoffRecords(self, club_pk=0, user=None):
        return DdClubRecord.query.from_statement(
            text(BEST_PLAYOFF_RECORD_SQL).params(
                userpk=user.pk,
                clubpk=club_pk
            )
        ).all()

    def GetRegularRecords(self, club_pk=0, user=None):
        return DdClubRecord.query.from_statement(
            text(BEST_REGULAR_RECORD_SQL).params(
                userpk=user.pk,
                clubpk=club_pk
            )
        ).all()

    def GetClubRecordsForUser(self, club_pk=0, user=None):
        return DdClubRecord.query.from_statement(
            text(CLUB_RECORDS_SQL).params(
                userpk=user.pk,
                clubpk=club_pk
            )
        ).all()


    def SaveClubRecord(self, club_record=None):
        db.session.add(club_record)
        db.session.commit()

    def SaveClubRecords(self, club_records=[]):
        db.session.add_all(club_records)
        db.session.commit()


def PlayoffRecordComparator(record):
    if record.last_playoff_series.top_seed_pk == record.club_pk:
        return record.last_playoff_series.GetTopSeedMatchesWon(
            DdLeagueConfig.SETS_TO_WIN
        )
    elif record.last_playoff_series.low_seed_pk == record.club_pk:
        return record.last_playoff_series.GetLowSeedMatchesWon(
            DdLeagueConfig.SETS_TO_WIN
        )

def RegularRecordComparator(record):
    return record.regular_season_points_n
