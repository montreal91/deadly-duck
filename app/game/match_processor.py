
from random import random

class DdMatchResult( object ):
    def __init__( self ):
        super( DdMatchResult, self ).__init__()
        self._full_score = ""
        self._home_sets = 0
        self._away_sets = 0
        self._home_games = 0
        self._away_games = 0

    @property
    def full_score( self ):
        return self._full_score

    @property
    def home_sets( self ):
        return self._home_sets

    @property
    def away_sets( self ):
        return self._away_sets

    @property
    def home_games( self ):
        return self._home_games

    @property
    def away_games( self ):
        return self._away_games

    def AddHomeSets( self, val ):
        self._home_sets += val

    def AddAwaySets( self, val ):
        self._away_sets += val

    def AddHomeGames( self, val ):
        self._home_games += val

    def AddAwayGames( self, val ):
        self._away_games += val

    def AppendSetToFullScore( self, home_games, away_games ):
        s = "{0:d}: {1:d}".format( home_games, away_games )
        if len( self._full_score ) > 0:
            self._full_score += " "
        self._full_score += s


class DdMatchProcessor( object ):
    @staticmethod
    def _IsSetOver( hgames, agames ):
        c1 = hgames >= 6 and hgames - agames >= 2
        c2 = agames >= 6 and agames - hgames >= 2

        return c1 or c2

    @staticmethod
    def _IsMatchOver( hsets, asets, sets_to_win ):
        return hsets == sets_to_win or asets == sets_to_win

    @staticmethod
    def _ProcessSet( home_player, away_player ):
        total = home_player.skill + away_player.skill
        home_prob = home_player.skill / total

        home_games, away_games = 0, 0
        while not DdMatchProcessor._IsSetOver( home_games, away_games ):
            toss = LoadedToss( home_prob )
            if toss:
                home_games += 1
            else:
                away_games += 1
        return home_games, away_games

    @staticmethod
    def ProcessMatch( home_player, away_player, sets_to_win ):
        res = DdMatchResult()
        while not DdMatchProcessor._IsMatchOver( res.home_sets, res.away_sets, 2 ):
            home_games, away_games = DdMatchProcessor._ProcessSet( home_player, away_player )
            res.AddHomeGames( home_games )
            res.AddAwayGames( away_games )
            res.AppendSetToFullScore( home_games, away_games )
            if home_games > away_games:
                res.AddHomeSets( 1 )
            else:
                res.AddAwaySets( 1 )
        return res

def LoadedToss( probability ):
    return random() < probability
