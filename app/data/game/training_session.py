
"""
This file contains helpers for training sessions.

Created on Jul 4, 2017

@author: montreal91
"""

from collections import namedtuple


# Immutable object which helps to store training type and intensity.
DdTraining = namedtuple( "DdTraining", field_names=["archetype", "intensity"] )

class DdTrainingSession( object ):
    """
    Thin wrapper over dictionary class which helps to organize user's players
    and their training sessions.
    """

    def __init__( self ):
        # Since players' pks are unique, they can be used as dictionary keys.
        self._training_sessions = {}

    @property
    def training_sessions( self ):
        return self._training_sessions

    def AddPlayerTraining( self, player_pk, training_type, training_intensity ):
        training = DdTraining( archetype=training_type, intensity=training_intensity )
        self._training_sessions[player_pk] = training
