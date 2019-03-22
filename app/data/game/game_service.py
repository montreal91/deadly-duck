
"""
This file contains one class: DdGameService. The purpose of this module is to
incapsulate all game logic and calls to the database.

Created on Nov 29, 2016

@author: montreal91
"""
from random import choice
from typing import List

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import db   # This import creates circular dependencies.
from app.custom_queries import GLOBAL_USER_RATING_SQL
from app.data.game.career import DdDaoCareer
from app.data.game.club import DdDaoClub
from app.data.game.match import DdDaoMatch
from app.data.game.match import DdMatchStatuses
from app.data.game.player import DdDaoPlayer
from app.data.game.player import DdPlayer
from app.data.game.playoff_series import DdDaoPlayoffSeries
from app.data.game.playoff_series import DdPlayoffSeries
from app.data.game.state_saver import AbortChanges
from app.data.game.state_saver import SaveObject
from app.data.game.state_saver import SaveObjects
from app.data.main.user import DdUser
from app.exceptions import BadUserInputException
from configuration.config_game import DdGameplayConstants
from configuration.config_game import DdLeagueConfig
from configuration.config_game import DdRatingsParamerers


class DdGameService:
    """One class to rule them all. Or to incapsulate game logic indeed.

    Everything related to game logic have to reside here.
    Game views should never acces data directly. Only through this class.
    """
    def __init__(self):
        self._dao_club = DdDaoClub()
        self._dao_match = DdDaoMatch()
        self._dao_player = DdDaoPlayer()
        self._dao_playoff_series = DdDaoPlayoffSeries()

    def AgeUpAllActivePlayers(self, user_pk) -> List[DdPlayer]:
        players = self._dao_player.GetAllActivePlayers(user_pk)
        for player in players:
            player.AgeUp()
        self._dao_player.SavePlayers(players)

    def CreateNewMatch(
        self,
        user_pk=0,
        season=0,
        day=0,
        home_team_pk=0,
        away_team_pk=0,
    ):
        return self._dao_match.CreateNewMatch(
            user_pk=user_pk,
            season=season,
            day=day,
            home_team_pk=home_team_pk,
            away_team_pk=away_team_pk
        )

    def CreateNewPlayoffRound(
        self,
        user=None,
        div1_list=[],
        div2_list=[],
        current_round=0,
        final=False
    ):
        assert len(div1_list) == len(div2_list)
        length = len(div1_list)
        if final:
            top, low = 0, 0
            recent_standings = self._dao_match.GetRecentStandings(user)
            if recent_standings.index(div1_list[0]) > recent_standings.index(div2_list[0]):
                top = div1_list[0]
                low = div2_list[0]
            elif recent_standings.index(div1_list[0]) < recent_standings.index(div2_list[0]):
                top = div2_list[0]
                low = div1_list[0]
            else:
                raise ValueError

            series = self._dao_playoff_series.CreatePlayoffSeries(
                top_seed_pk=top,
                low_seed_pk=low,
                round_n=current_round,
                user=user
            )
            self._dao_playoff_series.SavePlayoffSeries(series)
            self._CreateMatchesForSeriesList(
                series_list=[series],
                first_day=user.current_day_n + DdLeagueConfig.GAP_DAYS
            )
            return
        new_series = []
        for i in range(int(length / 2)):
            series = DdPlayoffSeries()
            series.top_seed_pk = div1_list[i]
            series.low_seed_pk = div1_list[length - i - 1]
            series.user_pk = user.pk
            series.season_n = user.current_season_n
            series.round_n = current_round
            new_series.append(series)

        for i in range(int(length / 2)):
            series = DdPlayoffSeries()
            series.top_seed_pk = div2_list[i]
            series.low_seed_pk = div2_list[length - i - 1]
            series.user_pk = user.pk
            series.season_n = user.current_season_n
            series.round_n = current_round
            new_series.append(series)

        self._dao_playoff_series.SavePlayoffSeriesList(new_series)
        self._CreateMatchesForSeriesList(
            series_list=new_series,
            first_day=user.current_day_n + DdLeagueConfig.GAP_DAYS
        )

    def DoesUserNeedToSelectPlayer(
            self, user: DdUser, selected_player: int
    ) -> bool:
        """Checks if user needs to select player for next match."""
        current_match = self.GetCurrentMatch(user)
        return current_match and selected_player is None

    def GetClub(self, club_pk):
        return self._dao_club.GetClub(club_pk)

    def GetAllActivePlayers(self, user_pk):
        return self._dao_player.GetAllActivePlayers(user_pk)

    def GetAllClubs(self):
        return self._dao_club.GetAllClubs()

    def GetAllClubsInDivision(self, division):
        return self._dao_club.GetAllClubsInDivision(division)

    def GetAllPlayoffSeries(self, user_pk, season):
        return self._dao_playoff_series.GetAllPlayoffSeries(user_pk, season)

    def GetClubPlayers(self, user_pk=0, club_pk=0):
        return self._dao_player.GetClubPlayers(user_pk=user_pk, club_pk=club_pk)

    def GetClubPlayersPks(self, user_pk=0, club_pk=0):
        return self._dao_player.GetClubPlayersPks(user_pk, club_pk)

    def GetCurrentMatch(self, user):
        return self._dao_match.GetCurrentMatch(user)

    def GetDayResults(self, user_pk, season, day):
        return self._dao_match.GetDayResults(user_pk, season, day)

    def GetDivisionStandings(self, user_pk=0, season=0, division=0):
        return self._dao_match.GetDivisionStandings(
            user_pk=user_pk,
            season=season,
            division=division
        )

    def GetFreeAgents(self, user_pk):
        return self._dao_player.GetFreeAgents(user_pk)

    def GetLeagueStandings(self, user_pk=0, season=0):
        return self._dao_match.GetLeagueStandings(
            user_pk=user_pk,
            season=season
        )

    def GetListOfClubPrimaryKeys(self):
        return self._dao_club.GetListOfClubPrimaryKeys()

    # TODO: move it to some DAO.
    # Service should not have direct access to database.
    # Because it causes cyclic imports!
    def GetGlobalRatings(self):
        return db.engine.execute(
            text(GLOBAL_USER_RATING_SQL).params(
                precision=DdRatingsParamerers.PRECISION,
                matches_coefficient=DdRatingsParamerers.MATCHES_COEFFICIENT,
                round_coefficient=DdRatingsParamerers.ROUND_COEFFICIENT,
                ground_level=DdRatingsParamerers.GROUND_LEVEL,
                regular_points_factor=DdRatingsParamerers.REGULAR_POINTS_FACTOR
            )
        ).fetchall()

    def GetMaxPlayoffRound(self, user=None):
        return self._dao_playoff_series.GetMaxPlayoffRound(user=user)

    def GetNumberOfActivePlayers(self):
        return self._dao_player.GetNumberOfActivePlayers()

    def GetNumberOfFinishedMatches(self):
        return self._dao_match.GetNumberOfFinishedMatches()

    def GetNumberOfFinishedSeries(self):
        return self._dao_playoff_series.GetNumberOfFinishedSeries()

    def GetPlayer(self, player_pk):
        return self._dao_player.GetPlayer(player_pk)

    def GetPlayoffSeries(self, series_pk=0):
        return self._dao_playoff_series.GetPlayoffSeries(series_pk=series_pk)

    def GetPlayoffSeriesByRoundAndDivision(self, user=None, rnd=0):
        return self._dao_playoff_series.GetPlayoffSeriesByRoundAndDivision(
            user=user,
            rnd=rnd
        )

    def GetPlayerRecentMatches(self, player_pk=0, season=0):
        return self._dao_player.GetPlayerRecentMatches(
            player_pk,
            season
        )

    def GetRemainingClubs(self, user):
        div1standings, div2standings = self._GetClubsQualifiedToPlayoffs(
            user=user
        )

        series_list = self.GetAllPlayoffSeries(
            user_pk=user.pk,
            season=user.current_season_n
        )
        if len(series_list) == 0:
            return div1standings, div2standings

        for series in series_list:
            l_pk = series.GetLooserPk(
                sets_to_win=DdLeagueConfig.SETS_TO_WIN,
                matches_to_win=DdLeagueConfig.MATCHES_TO_WIN
            )
            if l_pk is None:
                raise ValueError(
                    "Playoff series #{0:d} is not finished.".format(series.pk)
                )
            if l_pk in div1standings:
                div1standings.pop(div1standings.index(l_pk))
            elif l_pk in div2standings:
                div2standings.pop(div2standings.index(l_pk))
            else:
                raise ValueError(
                    "Club #{0:d} has lost in playoff series #{1:d} but not even qualified to playoffs.".format(
                        l_pk,
                        series.pk
                    )
                )
        return div1standings, div2standings

    def GetTodayMatches(self, user):
        return self._dao_match.GetTodayMatches(user)

    def InsertClubs(self):
        self._dao_club.InsertClubs()

    def IsNewRoundNeeded(self, user: DdUser) -> bool:
        """Checks if a new playoff round needs to be created for given user."""
        last = self._dao_match.GetLastMatchDay(user)
        return user.current_day_n > last + 1

    def NewSeasonCondition(self, d1: List, d2: List) -> bool:
        condition1 = len(d1) == 1 and len(d2) == 0
        condition2 = len(d2) == 1 and len(d1) == 0
        return condition1 or condition2

    def ProcessDailyRecovery(self, user_pk: int, played_players: List):
        """
        Restores stamina for active players of given user 'at the end of the day'.
        Important: saves changes to database.
        :param user_pk: primary key of user, whose players need to be recovered.
        :param played_players: list of players who was playing matches this day.
        """
        played_players_pks = [plr.pk_n for plr in played_players]
        players_to_update = []
        club_pks = self.GetListOfClubPrimaryKeys()
        for cpk in club_pks:
            club_players = self.GetClubPlayers(user_pk=user_pk, club_pk=cpk)
            for plr in club_players:
                if plr.current_stamina_n < plr.max_stamina and plr.pk_n not in played_players_pks:
                    players_to_update.append(plr)
        players_to_update += played_players
        for plr in players_to_update:
            plr.RecoverStamina(
                DdGameplayConstants.STAMINA_RECOVERY_PER_DAY.value
            )
        self.SavePlayers(players_to_update)

    def SaveMatch(self, match=None):
        self._dao_match.SaveMatch(match=match)

    def SaveMatches(self, matches: List):
        series_to_update = []
        for match in matches:
            series = match.playoff_series
            if series is None:
                # In case if it is not a playoffs match
                continue
            if series.top_seed_pk == match.home_team_pk:
                if match.home_sets_n > match.away_sets_n:
                    series.top_seed_victories_n += 1
                elif match.home_sets_n < match.away_sets_n:
                    series.low_seed_victories_n += 1
                else:
                    raise ValueError("Match score is incorrect. \n (Draw is impossible).")
            elif series.top_seed_pk == match.away_team_pk:
                if match.home_sets_n > match.away_sets_n:
                    series.low_seed_victories_n += 1
                elif match.home_sets_n < match.away_sets_n:
                    series.top_seed_victories_n += 1
                else:
                    raise ValueError("Match score is incorrect. \n (Draw is impossible).")
            else:
                raise ValueError

            series_to_update.append(series)
        self.SavePlayoffSeriesList(series_to_update)
        self._dao_match.SaveMatches(matches=matches)


    def SavePlayer(self, player):
        self._dao_player.SavePlayer(player)

    def SavePlayers(self, players):
        self._dao_player.SavePlayers(players)

    def SavePlayoffSeriesList(self, series_list: List):
        matches_to_abort = []
        for series in series_list:
            if not series.IsFinished(matches_to_win=DdLeagueConfig.MATCHES_TO_WIN):
                continue

            for match in series.matches:
                if match.status_en == DdMatchStatuses.planned:
                    match.status_en = DdMatchStatuses.aborted
                    matches_to_abort.append(match)

        self._dao_match.SaveMatches(matches=matches_to_abort)
        self._dao_playoff_series.SavePlayoffSeriesList(series_list=series_list)


    def SaveRosters(self, rosters):
        self._dao_player.SaveRosters(rosters)

    def StartNextSeason(self, user_pk):
        players = self._dao_player.GetAllActivePlayers(user_pk=user_pk)
        for player in players:
            player.AgeUp()
            player.AfterSeasonRest()

        clubs = self._dao_club.GetAllClubs()
        for club in clubs:
            active_players = [player for player in players if player.is_active and player.club_pk == club.club_id_n]
            new_players = self._CreateNewcomersForClub(
                user_pk=user_pk,
                club_pk=club.club_id_n,
                number=DdGameplayConstants.MAX_PLAYERS_IN_CLUB.value - len(active_players)
            )
            players += new_players
        self.SavePlayers(players=players)

    def StartNewCareer(self, user_pk: int, managed_club_pk: int):
        """Starts new career.

        If user_pk is invalid user key or if managed_club_pk is invalid
        club key, raises ``BadUserInputException``.
        """
        # TODO(montreal91) refactor it with use of context manager
        # TODO(montreal91) think if initial lists of players should be crated
        try:
            career = DdDaoCareer.CreateNewCareer(
                user_pk=user_pk,
                managed_club_pk=managed_club_pk
            )
            SaveObject(career)
        except IntegrityError:
            AbortChanges()
            raise BadUserInputException


    def _CreateMatchesForSeriesList(self, series_list: List, first_day: int):
        new_matches = []
        for series in series_list:
            shift = series_list.index(series) % 2
            for i in range(len(DdLeagueConfig.SERIES_TOP_HOME_PATTERN)):
                match = self._dao_match.CreateNewMatchForSeries(
                    series=series,
                    day=first_day + i * 2 + shift,
                    top_home=DdLeagueConfig.SERIES_TOP_HOME_PATTERN[i]
                )
                new_matches.append(match)
        self._dao_match.SaveMatches(new_matches)

    def _CreateNewcomersForClub(
        self, user_pk: int, club_pk: int, number: int
    ) -> List[DdPlayer]:
        players = []
        first_names, last_names = DdPlayer.GetNames()
        for i in range(number):
            player = self._dao_player.CreatePlayer(
                first_name=choice(first_names),
                second_name=choice(first_names),
                last_name=choice(last_names),
                user_pk=user_pk,
                club_pk=club_pk,
                technique=DdGameplayConstants.SKILL_BASE.value,
                endurance=DdGameplayConstants.SKILL_BASE.value,
                age=DdGameplayConstants.STARTING_AGE.value
            )
            players.append(player)
        return players

    def _GetClubsQualifiedToPlayoffs(self, user: DdUser):
        div1standings = [row.club_pk for row in self.GetDivisionStandings(user_pk=user.pk, season=user.current_season_n, division=1)]
        div2standings = [row.club_pk for row in self.GetDivisionStandings(user_pk=user.pk, season=user.current_season_n, division=2)]

        div1standings = div1standings[:DdLeagueConfig.DIV_CLUBS_IN_PLAYOFFS]
        div2standings = div2standings[:DdLeagueConfig.DIV_CLUBS_IN_PLAYOFFS]
        return div1standings, div2standings

    def _MatchIncome(self, sets=0):
        """Placeholder function.

        Financial side of the game is yet to be developed.
        """
        if sets == 2:
            return 1000
        elif sets == 1:
            return 700
        elif sets == 0:
            return 450
        else:
            raise ValueError("Incorrect number of sets.")

    def _ProcessTrainingSessionForPlayer(self, player):
        player.AddExperience(DdGameplayConstants.EXPERIENCE_PER_TRAINING.value)

