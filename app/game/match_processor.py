
from collections import namedtuple
from decimal import Decimal
from enum import Enum
from random import randint

from config_game import sets_to_win
from stat_tools import LoadedToss

DdSetResult = namedtuple( 
    "DdSetResult", [
        "home_games",
        "away_games",
        "set_status",
    ],
    rename=True
 )


class DdSetStatuses( Enum ):
    REGULAR = 1
    HOME_RETIRED = 2
    AWAY_RETIRED = 3


class DdMatchResult( object ):
    def __init__( self ):
        super( DdMatchResult, self ).__init__()
        self._full_score = ""
        self._home_sets = 0
        self._away_sets = 0
        self._home_games = 0
        self._away_games = 0
        self._home_stamina_lost = 0
        self._away_stamina_lost = 0


    @property
    def away_games( self ):
        return self._away_games

    @property
    def away_sets( self ):
        return self._away_sets

    @away_sets.setter
    def away_sets( self, value ):
        """
        This setter should be used only to deal exceptional match result.
        """
        assert value >= 0, "Number of sets should be greater than 0."
        assert value <= sets_to_win, "Number of sets should be lesser than %r." % sets_to_win
        self._away_sets = int( value )

    @property
    def away_stamina_lost( self ):
        return self._away_stamina_lost

    @property
    def full_score( self ):
        return self._full_score

    @property
    def home_games( self ):
        return self._home_games

    @property
    def home_sets( self ):
        return self._home_sets

    @home_sets.setter
    def home_sets( self, value ):
        """
        This setter should be used only to deal exceptional match result.
        """
        assert value >= 0, "Number of sets should be greater than 0."
        assert value <= sets_to_win, "Number of sets should be lesser than %r." % sets_to_win
        self._home_sets = int( value )

    @property
    def home_stamina_lost( self ):
        return self._home_stamina_lost

    def AddHomeGames( self, val ):
        self._home_games += val

    def AddHomeSets( self, val ):
        self._home_sets += val

    def AddHomeStaminaLost( self, val ):
        self._home_stamina_lost += val

    def AddAwayGames( self, val ):
        self._away_games += val

    def AddAwaySets( self, val ):
        self._away_sets += val

    def AddAwayStaminaLost( self, val ):
        self._away_stamina_lost += val

    def AppendSetToFullScore( self, set_result ):
        s = "{0:d}:{1:d}".format( set_result.home_games, set_result.away_games )
        if set_result.set_status == DdSetStatuses.HOME_RETIRED:
            s += " Rt:W"
        elif set_result.set_status == DdSetStatuses.AWAY_RETIRED:
            s += " W:Rt"

        if len( self._full_score ) > 0:
            self._full_score += " "
        self._full_score += s


class DdMatchProcessor( object ):
    def __init__( self ):
        self._res = DdMatchResult()

    def ProcessMatch( self, home_player, away_player, sets_to_win=2 ):
        while not self._IsMatchOver( self._res.home_sets, self._res.away_sets, sets_to_win ):
            set_result = self._ProcessSet( 
                home_player,
                away_player
            )
            self._res.AddHomeGames( set_result.home_games )
            self._res.AddAwayGames( set_result.away_games )
            self._res.AppendSetToFullScore( 
                set_result
            )
            if set_result.home_games > set_result.away_games:
                self._res.AddHomeSets( 1 )
            else:
                self._res.AddAwaySets( 1 )

            if set_result.set_status == DdSetStatuses.HOME_RETIRED:
                self._res.away_sets = sets_to_win
                self._res.home_sets = 0
                break
            elif set_result.set_status == DdSetStatuses.AWAY_RETIRED:
                self._res.home_sets = sets_to_win
                self._res.away_sets = 0
                break

        return self._res

    def _CalculateActualSkill( self, player, actual_stamina=0 ):
        max_stamina = player.max_stamina
        stamina_factor = actual_stamina / Decimal( max_stamina )
        return Decimal( player.technique.current_maximum_n ) * stamina_factor

    def _CalculateActualStamina( self, player, lost_stamina=0 ):
        actual_stamina = Decimal( player.current_stamina_n ) - Decimal( lost_stamina )
        if actual_stamina < 0:
            return 0
        else:
            return actual_stamina

    def _CalculateStaminaLostInGame( self ):
        return randint( 1, 3 ) * 0.75

    def _IsSetOver( self, hgames, agames ):
        c1 = hgames >= 6 and hgames - agames >= 2
        c2 = agames >= 6 and agames - hgames >= 2

        return c1 or c2

    def _IsMatchOver( self, hsets, asets, sets_to_win ):
        return hsets == sets_to_win or asets == sets_to_win

    def _ProcessSet( self, home_player, away_player ):
        home_games, away_games = 0, 0
        while not self._IsSetOver( home_games, away_games ):
            home_stamina = self._CalculateActualStamina( 
                home_player,
                lost_stamina=self._res.home_stamina_lost
            )
            away_stamina = self._CalculateActualStamina( 
                away_player,
                lost_stamina=self._res.away_stamina_lost
            )
            home_actual_skill = self._CalculateActualSkill( home_player, home_stamina )
            away_actual_skill = self._CalculateActualSkill( away_player, away_stamina )

            if home_actual_skill == 0:
                return DdSetResult( 
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.HOME_RETIRED
                )
            elif away_actual_skill == 0:
                return DdSetResult( 
                    home_games=home_games,
                    away_games=away_games,
                    set_status=DdSetStatuses.AWAY_RETIRED
                )

            total_skill = home_actual_skill + away_actual_skill
            home_prob = home_actual_skill / total_skill
            toss = LoadedToss( home_prob )
            if toss:
                home_games += 1
            else:
                away_games += 1
            self._res.AddHomeStaminaLost( self._CalculateStaminaLostInGame() )
            self._res.AddAwayStaminaLost( self._CalculateStaminaLostInGame() )

        return DdSetResult( 
            home_games=home_games,
            away_games=away_games,
            set_status=DdSetStatuses.REGULAR,
        )
