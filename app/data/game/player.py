
import json
import math

from decimal import Decimal
from random import randint

from sqlalchemy import and_
from sqlalchemy import text

from app import db
from app.custom_queries import RECENT_PLAYER_MATCHES_SQL
from app.data.game.match import DdMatchSnapshot
from configuration.config_game import number_of_recent_matches
from configuration.config_game import DdGameplayConstants
from configuration.config_game import DdPlayerSkills


class DdPlayer(db.Model):
    __tablename__ = "players"
    pk_n = db.Column(db.Integer, primary_key=True)
    first_name_c = db.Column(db.String(64), nullable=False)
    second_name_c = db.Column(db.String(64))
    last_name_c = db.Column(db.String(64), nullable=False)

    technique_n = db.Column(db.Integer, default=50)
    endurance_n = db.Column(db.Integer, default=50)
    experience_n = db.Column(db.Integer, default=0)
    exhaustion_n = db.Column(db.Integer, default=0)
    abilities_c = db.Column(db.String(6), default="000000")
    current_stamina_n = db.Column(db.Integer, default=100)
    age_n = db.Column(db.Integer, default=20)
    is_active = db.Column(db.Boolean, default=True)

    user_pk = db.Column(db.Integer, db.ForeignKey("users.pk"))
    club_pk = db.Column(db.Integer, db.ForeignKey("clubs.club_id_n"))

    user = db.relationship("DdUser", foreign_keys=[user_pk], lazy="subquery")
    club = db.relationship("DdClub", foreign_keys=[club_pk], lazy="subquery")

    @property
    def actual_technique(self):
        stamina_factor = self.current_stamina_n / self.max_stamina
        return round(self.technique_n * stamina_factor / 10, 1)

    @property
    def endurance(self):
        return round(self.endurance_n / 10, 1)


    @property
    def full_name(self):
        return self.first_name_c + " " + self.second_name_c + " " + self.last_name_c

    @property
    def level(self):
        skill_points = self.technique_n + self.endurance_n
        skill_points -= DdGameplayConstants.SKILL_BASE.value * 2
        return int(skill_points / DdGameplayConstants.SKILL_GROWTH_PER_LEVEL.value)

    # 'exp' stands for experience
    @property
    def next_level_exp(self):
        next_level = self.level + 1
        lvl_sum = next_level / 2 * (next_level + 1)
        return int(lvl_sum * DdGameplayConstants.LEVEL_EXPERIENCE_COEFFICIENT.value)

    @property
    def match_salary(self):
        return DdPlayer.CalculateSalary(
            skill=self.technique.current_maximum_n,
            age=self.age_n
        )

    @property
    def max_stamina(self):
        return self.endurance_n * DdPlayerSkills.ENDURANCE_FACTOR


    @property
    def passive_salary(self):
        res = DdPlayer.CalculateSalary(
            skill=self.technique.current_maximum_n,
            age=self.age_n
        )
        return round(res / 2, 2)

    @property
    def technique(self):
        return self.technique_n / 10

    def AddExperience(self, experience):
        self.experience_n += experience

    def AfterSeasonRest(self):
        self.exhaustion_n = 0
        self.RecoverStamina(self.max_stamina)

    def AgeUp(self):
        self.age_n += 1
        if self.age_n >= DdGameplayConstants.RETIREMENT_AGE.value:
            self.is_active = False


    def LevelUpAuto(self):
        while self.experience_n >= self.next_level_exp:
            toss = randint(0, 1)
            if toss:
                self.technique_n += DdGameplayConstants.SKILL_GROWTH_PER_LEVEL.value
            else:
                self.endurance_n += DdGameplayConstants.SKILL_GROWTH_PER_LEVEL.value

    def RecoverStamina(self, recovered_stamina=0):
        self.current_stamina_n += recovered_stamina
        if self.current_stamina_n > self.max_stamina:
            self.current_stamina_n = self.max_stamina

    def RemoveStaminaLostInMatch(self, lost_stamina=0):
        self.current_stamina_n -= lost_stamina

    @staticmethod
    def CalculateNewExperience(sets_won, opponent):
        base = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value * sets_won
        factor = DdGameplayConstants.EXPERIENCE_LEVEL_FACTOR.value
        factor *= opponent.level
        factor /= 100 # 100%
        factor += 1
        return round(base * factor)


    @staticmethod
    def CalculateSalary(skill=0, age=0):
        return 100

    @staticmethod
    def GetNames():
        with open("configuration/names.json") as datafile:
            all_names = json.load(datafile)
        return all_names["names"], all_names["surnames"]

    def __repr__(self):
        return "<Player {0:d} {1}. {2}. {3}>".format(
            self.pk_n,
            self.first_name_c[0],
            self.second_name_c[0],
            self.last_name_c
        )


class DdDaoPlayer(object):
    """
    Data Access Object for DdPlayer class
    """
    def CreatePlayer(
        self,
        first_name="",
        second_name="",
        last_name="",
        user_pk=0,
        club_pk=None,
        endurance=50,
        technique=50,
        age=10,
    ):
        player = DdPlayer()
        player.first_name_c = first_name
        player.second_name_c = second_name
        player.last_name_c = last_name
        player.user_pk = user_pk
        player.club_pk = club_pk
        player.endurance_n = endurance
        player.technique_n = technique
        player.current_stamina_n = endurance
        player.age_n = age
        return player

    def GetAllActivePlayers(self, user_pk=0):
        return DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_active == True
            )
        ).all()

    def GetClubPlayers(self, user_pk=0, club_pk=0):
        qres = DdPlayer.query.filter(and_(
            DdPlayer.club_pk == club_pk,
            DdPlayer.user_pk == user_pk,
            DdPlayer.is_active == True,
        ))
        return qres.all()

    def GetFreeAgents(self, user_pk):
        res = DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user_pk,
                DdPlayer.club_pk == None,
                DdPlayer.is_active == True,
            )
        )
        return res.all()

    def GetNumberOfActivePlayers(self):
        return DdPlayer.query.filter_by(is_active=True).count()

    def GetNumberOfUndraftedPlayers(self, user_pk: int) -> int:
        return DdPlayer.query.filter(
            and_(
                DdPlayer.user_pk == user_pk,
                DdPlayer.is_drafted == False
            )
        ).count()

    def GetPlayer(self, player_pk):
        return DdPlayer.query.get(player_pk)

    def GetPlayerRecentMatches(self, player_pk, season):
        query_res = db.engine.execute(
            RECENT_PLAYER_MATCHES_SQL.format(
                player_pk,
                season,
                number_of_recent_matches
            )
        ).fetchall()
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

    def SavePlayer(self, player):
        db.session.add(player)
        db.session.commit()

    def SavePlayers(self, players):
        db.session.add_all(players)
        db.session.commit()

    def SaveRosters(self, rosters):
        players = []
        for club_pk in rosters:
            for plr in rosters[club_pk]:
                player = DdPlayer.query.get(plr.pk)
                player.club_pk = club_pk
                player.is_drafted = True
                players.append(player)
        db.session.add_all(players)
        db.session.commit()


def PlayerModelComparator(player_model):
    return player_model.actual_technique * 1.2 + player_model.endurance
