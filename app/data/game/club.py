
from typing import List

from sqlalchemy import text

from app import db
from app.custom_queries import CLUB_PKS_SQL
from configuration.config_game import club_names


class DdClub(db.Model):
    __tablename__ = "clubs"
    pk = db.Column(db.Integer, primary_key=True)
    club_name_c = db.Column(db.String(64))
    division_n = db.Column(db.Integer)

    def __repr__(self):
        return "<Club %r>" % self.club_name_c


class DdDaoClub(object):
    def GetAllClubs(self):
        return DdClub.query.all()

    def GetAllClubsInDivision(self, division):
        return DdClub.query.filter_by(division_n=division).all()

    def GetClub(self, club_pk):
        return DdClub.query.get_or_404(club_pk)

    def GetListOfClubPrimaryKeys(self) -> List[int]:
        qres = db.engine.execute(text(CLUB_PKS_SQL)).fetchall()
        return tuple(row['pk'] for row in qres)

    def InsertClubs(self):
        new_clubs = []
        for div in  club_names:
            for name in club_names[div]:
                club = DdClub()
                club.club_name_c = name
                club.division_n = div
                new_clubs.append(club)
        db.session.add_all(new_clubs)
        db.session.commit()
