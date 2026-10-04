"""
Created September 22, 2026

@author montreal91
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    game_id: str
    club_id: str
    player_id: str
    season_index: int
    contract_cost: int
    status: str
