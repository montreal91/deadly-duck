
from app import db


class DdCareer(db.Model):
    __tablename__ = "careers"
    pk = db.Column(db.Integer, primary_key=True)
    title_c = db.Column(db.String(100))
    managed_club_pk = db.Column(
        db.Integer, db.ForeignKey("clubs.pk"), nullable=False
    )

    user_pk = db.Column(db.Integer, db.ForeignKey("users.pk"), nullable=False)
    user = db.relationship("DdUser", foreign_keys=[user_pk], backref="careers")

    season_n = db.Column(db.Integer, default=0)
    day_n = db.Column(db.Integer, default=0)
