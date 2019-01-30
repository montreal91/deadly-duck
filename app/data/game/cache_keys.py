'''
Created on Jun 26, 2017

@author: montreal91

This module contains all cache keys used in DdGameService
'''

from enum import Enum


class DdGameCacheKeys(Enum):
    """
    Enum which contains keys which are not specific for any model
    """
    DRAFT_FOR_PLAYER = "draft[{user_pk}]"
    DRAFTER = "drafter[{user_pk}]"
    SELECTED_PLAYER = "selected_player[{user_pk}]"
    TRAINING_SESSION = "training_session[{user_pk}]"


class DdPlayerCacheKeys(Enum):
    """
    This enum contains player-related keys.
    """
    ACTIVE_PLAYERS = "active_players[{user_pk}]"
    CLUB_PLAYERS = "club_players[{user_pk},{club_pk}]"
    FREE_AGENTS = "free_agents[{user_pk}]"
    NEWCOMERS = "newcomers[{user_pk}]"
    NUMBER_OF_NEWCOMERS = "number_of_newcomers[{user_pk}]"
    PLAYER = "player[{player_pk}]"
