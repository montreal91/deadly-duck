
import json
import math

from decimal import Decimal
from random import choice
from random import randint
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from sqlalchemy import and_
from sqlalchemy import text

from app import db
from app.custom_queries import RECENT_PLAYER_MATCHES_SQL
from app.data.game.match import DdMatchSnapshot
from configuration.config_game import number_of_recent_matches
from configuration.config_game import DdGameplayConstants
from configuration.config_game import DdPlayerSkills


class DdPlayer(db.Model):
    """Model that stores all player-related data in the database.

    Also contains all direct player-related logic.
    """
    __tablename__ = "players"
    pk = db.Column(db.Integer, primary_key=True)
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

    career_pk = db.Column(db.Integer, db.ForeignKey("careers.pk"))

    club_pk = db.Column(db.Integer, db.ForeignKey("clubs.pk"))
    club = db.relationship("DdClub", foreign_keys=[club_pk], lazy="subquery")

    @property
    def actual_technique(self) -> float:
        stamina_factor = self.current_stamina_n / self.max_stamina
        return round(self.technique_n * stamina_factor / 10, 1)

    @property
    def endurance(self):
        return round(self.endurance_n / 10, 1)

    @property
    def full_name(self):
        return self.first_name_c + " " + self.second_name_c + " " + self.last_name_c

    @property
    def json(self) -> Dict:
        """Returns a dictionary with json-serializable data."""
        return dict(
            pk=self.pk_n,
            first_name=self.first_name_c,
            second_name=self.second_name_c,
            last_name=self.last_name_c,
            technique=self.technique,
            endurance=self.endurance,
            actual_technique=self.actual_technique,
            level=self.level,
            age=self.age_n,
        )


    @property
    def level(self) -> int:
        """Current level of the player."""
        level = 0
        while _LevelExp(level) < self.experience_n:
            level += 1
        return level

    # 'exp' stands for experience
    @property
    def next_level_exp(self):
        return _LevelExp(self.level + 1)

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

    def AddExperience(self, experience: int):
        """Adds new experience.

        If necessary, levels up player.
        """
        old_level = self.level
        self.experience_n += experience
        new_level = self.level

        skill_delta = DdGameplayConstants.SKILL_GROWTH_PER_LEVEL.value
        while old_level < new_level:
            old_level += 1
            toss = randint(0, 1)
            if toss:
                self.technique_n += skill_delta
            else:
                self.endurance_n += skill_delta

    def AfterSeasonRest(self):
        self.exhaustion_n = 0
        self.RecoverStamina(self.max_stamina)

    def AgeUp(self):
        self.age_n += 1
        if self.age_n >= DdGameplayConstants.RETIREMENT_AGE.value:
            self.is_active = False

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

    def __repr__(self):
        return "<Player {0:d} {1}. {2}. {3}>".format(
            self.pk_n,
            self.first_name_c[0],
            self.second_name_c[0],
            self.last_name_c
        )


class DdDaoPlayer:
    """Data Access Object for DdPlayer class."""
    def __init__(self):
        self._first_names = None
        self._last_names = None

    @property
    def names(self) -> Tuple[List[str], List[str]]:
        """Couple of lists of strings for first and last names."""

        if self._first_names is None:
            self._first_names, self._last_names = _LoadNames()
        return self._first_names, self._last_names

    def CreatePlayer(
        self, career_pk: int, club_pk: Optional[int], level: int, age: int,
    ) -> DdPlayer:
        """
        Creates a player object with given parameters.

        Does not save anything in the database.
        """
        player = DdPlayer()
        player.first_name_c = choice(self.names[0])
        player.second_name_c = choice(self.names[0])
        player.last_name_c = choice(self.names[1])
        player.age_n = age
        player.career_pk = career_pk
        player.club_pk = club_pk

        skill_base = DdGameplayConstants.SKILL_BASE.value
        player.endurance_n = skill_base
        player.technique_n = skill_base
        player.exhaustion_n = 0
        player.experience_n = 0
        player.AddExperience(_LevelExp(level))
        player.current_stamina_n = player.max_stamina
        return player

    def CreateInitialClubPlayers(
        self, career_pk: int, club_pk: int
    ) -> List[DdPlayer]:
        """Creates default list of users at the beginning of the career."""
        first_names, last_names = self._names
        players = []
        for i in range(DdGameplayConstants.MAX_PLAYERS_IN_CLUB.value):
            player = self._dao_player.CreatePlayer(
                first_name=choice(first_names),
                second_name=choice(first_names),
                last_name=choice(last_names),
                user_pk=user_pk,
                club_pk=club.club_id_n,
                age=DdGameplayConstants.STARTING_AGE.value + i
            )
            player.AddExperience(_LevelExp(i * 2))
            players.append(player)
        return players

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

    # TODO(montreal91): Move to DdDaoMatch
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


def PlayerModelComparator(player_model):
    """Function used to compare two players."""
    return player_model.actual_technique * 1.2 + player_model.endurance


def _LevelExp(n: int) -> int:
    """Total experience required to gain a level.

    Formula is based on the sum of arithmetic progression.
    """
    ec = DdGameplayConstants.EXPERIENCE_COEFFICIENT.value
    return int((n * (n + 1) / 2) * ec)

def _LoadNames() -> Tuple[List[str], List[str]]:
    """Utility function that loads names from the file on the disk."""
    with open("configuration/names.json") as datafile:
        all_names = json.load(datafile)
    return all_names["names"], all_names["surnames"]
