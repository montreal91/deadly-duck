
from random                 import shuffle

from .                      import game
from ..                     import db
from app.data.game.club     import DdClub
from app.game.game_context  import DdGameContext
from config_game            import DdLeagueConfig, club_names


class DdLeague( object ):
    @staticmethod
    def AddRostersToContext( user, ctx=DdGameContext() ):
        clubs = game.service.GetAllClubs()
        for club in clubs:
            players = game.service.GetClubPlayers( user_pk=user.pk, club_pk=club.club_id_n )
            ctx.SetClubRoster( club_pk=club.club_id_n, players_list=players )
        game.contexts[user.pk] = ctx

    @staticmethod
    def CreateScheduleForUser( user ):
        divisions = dict()
        current_season = user.current_season_n
        for div in club_names:
            divisions[div] = DdClub.query.filter_by( division_n=div ).all()

        indiv = DdLeague._CreateIntraDivMatches( 
            divisions,
            DdLeagueConfig.INDIV_MATCHES
        )
        exdiv = DdLeague._CreateExtraDivMatches( 
            divisions,
            DdLeagueConfig.EXDIV_MATCHES
        )
        matches = indiv + exdiv
        shuffle( matches )

        playing_clubs = []
        db_matches = []

        for match in matches:
            day = 0
            scheduled = False
            while not scheduled:
                if day == len( playing_clubs ):
                    playing_clubs.append( set() )
                    playing_clubs[day].add( match[0] )
                    playing_clubs[day].add( match[1] )
                    db_match = game.service.CreateNewMatch( 
                        user_pk=user.pk,
                        season=current_season,
                        day=day,
                        home_team_pk=match[0],
                        away_team_pk=match[1]
                    )
                    db_matches.append( db_match )
                    scheduled = True
                elif match[0] not in playing_clubs[day] and match[1] not in playing_clubs[day]:
                    playing_clubs[day].add( match[0] )
                    playing_clubs[day].add( match[1] )
                    db_match = game.service.CreateNewMatch( 
                        user_pk=user.pk,
                        season=current_season,
                        day=day,
                        home_team_pk=match[0],
                        away_team_pk=match[1]
                    )
                    db_matches.append( db_match )
                    scheduled = True
                else:
                    day += 1
        game.service.SaveMatches( matches=db_matches )

    @staticmethod
    def StartDraft( user, context, need_to_create_newcomers=True ):
        context.is_draft = True
        if need_to_create_newcomers:
            game.service.CreateNewcomersForUser( user )

        newcomers = game.service.GetNewcomersSnapshotsForUser( user )
        context.newcomers = newcomers
        context.DropPickPointer()
        standings = game.service.GetRecentStandings( user )
        context.SetStandings( standings )
        game.contexts[user.pk] = context

    @staticmethod
    def StartNextSeason( user ):
        user.current_season_n += 1
        user.current_day_n = 0
        game.service.AgeUpAllActivePlayers( user )
        db.session.add( user )
        db.session.commit()
        DdLeague.CreateScheduleForUser( user )
        game.contexts[user.pk] = DdGameContext()
        DdLeague.AddRostersToContext( user )


    @staticmethod
    def _CreateExtraDivMatches( divisions, exdiv_matches ):
        """
        Creates list of matches played by clubs in different divisions.
        :rtype: list
        """
        matches_l = []
        same_matches = int( exdiv_matches / 2 )
        for div1 in divisions:
            for div2 in divisions:
                if div1 != div2:
                    matches_l += DdLeague._MakeMatchesBetweenDivisions( 
                        divisions[div1],
                        divisions[div2],
                        same_matches
                    )
        return matches_l


    @staticmethod
    def _CreateIntraDivMatches( divisions, indiv_matches ):
        """
        Generates list of matches inside all divisions.
        :rtype: list
        """
        matches_l = []
        same_matches = int( indiv_matches / 2 )
        for division in divisions:
            matches_l += DdLeague._MakeMatchesInsideDivision( 
                divisions[division],
                same_matches
            )
        return matches_l


    @staticmethod
    def _MakeMatchesBetweenDivisions( div1, div2, same_matches ):
        """
        Generates list of matches between clubs in two different divisions.
        :type div1: list
        :type div2: list
        :type same_matches: int
        :rtype: list
        """
        res = []
        for team1 in div1:
            for team2 in div2:
                res += [( team1.club_id_n, team2.club_id_n ) for k in range( same_matches )]
        return res


    @staticmethod
    def _MakeMatchesInsideDivision( division, same_matches ):
        """
        Creates list of games played by clubs in the same divisions.
        :type division: list
        :type same_matches: int
        """
        res = []
        for team1 in division:
            for team2 in division:
                if team1 != team2:
                    res += [( team1.club_id_n, team2.club_id_n ) for k in range( same_matches )]
        return res
