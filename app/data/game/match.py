
import json

from collections import namedtuple
from typing import List
from typing import NamedTuple
from typing import Optional

from sqlalchemy import and_
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app import db
from app.custom_queries import CURRENT_MATCH_SQL
from app.custom_queries import DAY_RESULTS_SQL
from app.custom_queries import MAX_DAY_IN_SEASON_SQL
from app.custom_queries import STANDINGS_FOR_DIVISION_SQL
from app.custom_queries import STANDINGS_SQL
from app.data.main.user import DdUser


class DdMatchStatuses:
    planned = "planned"
    finished = "finished"
    aborted = "aborted"


class DdMatchSnapshot(NamedTuple):
    """Lightweight passive data class for DdMatch model."""
    pk: int
    home_team: str
    home_team_pk: int
    away_team: str
    away_team_pk: int
    home_player: str
    away_player: str
    home_skill: int
    away_skill: int
    full_score: str

    @property
    def json(self):
        """Returns a dictionary with json-serializable data."""
        res = {}
        for field in self._fields:
            res[field] = getattr(self, field)
        return res


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


class DdMatch(db.Model):
    """Database model for one tennis match."""
    __tablename__ = "matches"
    match_pk_n = db.Column(db.Integer, primary_key=True, index=True)
    home_team_pk = db.Column(
        db.Integer, db.ForeignKey("clubs.club_id_n"), index=True
    )
    away_team_pk = db.Column(
        db.Integer, db.ForeignKey("clubs.club_id_n"), index=True
    )
    user_pk = db.Column(db.Integer, db.ForeignKey("users.pk"), index=True)
    home_player_pk = db.Column(
        db.Integer, db.ForeignKey("players.pk_n"), nullable=True, index=True
    )
    away_player_pk = db.Column(
        db.Integer, db.ForeignKey("players.pk_n"), nullable=True, index=True
    )
    season_n = db.Column(db.Integer, default=0, index=True)
    day_n = db.Column(db.Integer, default=0, index=True)

    # TODO(montreal91) Remove this redundant comumn.
    context_json = db.Column(db.Text)
    status_en = db.Column(
        postgresql.ENUM(
            DdMatchStatuses.planned,
            DdMatchStatuses.finished,
            DdMatchStatuses.aborted,
            name="match_status"
        ),
        nullable=False,
        default=DdMatchStatuses.planned,
    )

    playoff_series_pk = db.Column(
        db.Integer, db.ForeignKey("playoff_series.pk")
    )

    home_sets_n = db.Column(db.Integer, default=0)
    away_sets_n = db.Column(db.Integer, default=0)
    home_games_n = db.Column(db.Integer, default=0)
    away_games_n = db.Column(db.Integer, default=0)
    full_score_c = db.Column(db.String(128), default="")

    home_club = db.relationship("DdClub", foreign_keys=[home_team_pk])
    away_club = db.relationship("DdClub", foreign_keys=[away_team_pk])
    home_player = db.relationship("DdPlayer", foreign_keys=[home_player_pk])
    away_player = db.relationship("DdPlayer", foreign_keys=[away_player_pk])

    @property
    def winner_pk(self) -> Optional[int]:
        """If match is finished, returns a pk of the winner."""
        if self.status_en != DdMatchStatuses.finished:
            return None
        if self.home_sets_n > self.away_sets_n:
            return self.home_team_pk
        return self.away_team_pk

    def SetAbortedStatus(self):
        self.status_en = DdMatchStatuses.aborted

    def SetFinishedStatus(self):
        self.status_en = DdMatchStatuses.finished

    def SetPlannedStatus(self):
        self.status_en = DdMatchStatuses.planned

    def __repr__(self):
        return "<Match #{0:d} {1:d} vs {2:d}>".format(
            self.match_pk_n,
            self.home_team_pk,
            self.away_team_pk
        )


class DdDaoMatch(object):
    def CreateNewMatch(
            self,
            user_pk=0,
            season=0,
            day=0,
            home_team_pk=0,
            away_team_pk=0,
    ) -> DdMatch:
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

    def CreateNewMatchForSeries(
            self, series=None, day=0, top_home=True
        ) -> DdMatch:
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

    def GetCurrentMatch(self, user):
        match = db.engine.execute(
            CURRENT_MATCH_SQL.format(
                user.managed_club_pk,
                user.current_season_n,
                user.current_day_n,
                user.pk
            )
        ).first()
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

    def GetDayResults(self, user_pk, season, day):
        query_res = db.engine.execute(
            text(DAY_RESULTS_SQL).params(
                userpk=user_pk,
                season=season,
                day=day
            )
        ).fetchall()
        return [
            DdMatchSnapshot(
                pk=row["match_pk_n"],
                home_team=row["home_club"],
                away_team=row["away_club"],
                home_player=row["home_player"],
                away_player=row["away_player"],
                home_skill="",
                away_skill="",
                full_score=row["full_score_c"],
                home_team_pk=row["home_team_pk"],
                away_team_pk=row["away_team_pk"]
            )
            for row in query_res
        ]

    def GetDivisionStandings(self, user_pk=0, season=0, division=0):
        table = db.engine.execute(
            text(STANDINGS_FOR_DIVISION_SQL).params(
                season=season,
                user=user_pk,
                division=division,
            )
        ).fetchall()
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

    def GetLastMatchDay(self, user: DdUser) -> int:
        """Returns last day in season for given user."""
        query_res = db.engine.execute(text(MAX_DAY_IN_SEASON_SQL).params(
            user=user.pk, season=user.current_season_n
        )).first()
        return query_res[0]

    def GetLeagueStandings(self, user_pk=0, season=0):
        table = db.engine.execute(
            text(STANDINGS_SQL).params(season=season, user=user_pk)
        ).fetchall()
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

    def GetRecentStandings(self, user: DdUser):
        table = db.engine.execute(text(STANDINGS_SQL).params(
            season=user.current_season_n, user=user.pk
        )).fetchall()
        return [row[0] for row in reversed(table)]


    def GetNumberOfFinishedMatches(self) -> int:
        return DdMatch.query.filter_by(
            status_en=DdMatchStatuses.finished
        ).count()

    def GetTodayMatches(self, user):
        return DdMatch.query.filter(
            and_(
                DdMatch.season_n == user.current_season_n,
                DdMatch.day_n == user.current_day_n,
                DdMatch.user_pk == user.pk,
                DdMatch.status_en == DdMatchStatuses.planned
            )
        ).all()

    def SaveMatch(self, match: DdMatch):
        db.session.add(match)
        db.session.commit()

    def SaveMatches(self, matches: List[DdMatch]):
        db.session.add_all(matches)
        db.session.commit()


def MatchChronologicalComparator(match: DdMatch) -> DdMatch:
    return match.day_n
