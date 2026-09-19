"""
Created September 19, 2026

@author montreal91

Expected data for the clubs included in a newly created game.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedInitialClub:
    club_id: str
    name: str
    coach_power: int
    balance: int
    player_count: int
    contracted_player_count: int


INITIAL_CLUBS = (
    ExpectedInitialClub("auckland_aces", "Auckland Aces", 3, 1_000_000, 2, 2),
    ExpectedInitialClub("brisbane_vipers", "Brisbane Vipers", 1, 1_000_000, 2, 2),
    ExpectedInitialClub("canberra_masters", "Canberra Masters", 3, 500_000, 2, 2),
    ExpectedInitialClub("dandenong_pianists", "Dandenong Pianists", 2, 5_000_000, 3, 3),
    ExpectedInitialClub("melbourne_rockets", "Melbourne Rockets", 3, 1_120_000, 2, 2),
    ExpectedInitialClub("sydney_hearts", "Sydney Hearts", 3, 100_000, 2, 2),
    ExpectedInitialClub("sydney_queens", "Sydney Queens", 2, 1_700_000, 2, 2),
    ExpectedInitialClub("tasmanian_devils", "Tasmanian Devils", 2, 2_500_000, 2, 2),
    ExpectedInitialClub("adelaide_falcons", "Adelaide Falcons", 2, 1_100_000, 2, 2),
    ExpectedInitialClub("saigon_suns", "Saigon Suns", 1, 3_500_000, 2, 2),
    ExpectedInitialClub("darwin_ducks", "Darwin Ducks", 3, 3_500_000, 4, 4),
    ExpectedInitialClub("jakarta_jaguars", "Jakarta Jaguars", 1, 4_500_000, 2, 2),
    ExpectedInitialClub("perth_punks", "Perth Punks", 3, 550_000, 2, 2),
    ExpectedInitialClub("hong_kong_netrunners", "Hong Kong Netrunners", 1, 2_750_000, 1, 1),
    ExpectedInitialClub("melbourne_tech", "Melbourne Tech", 2, 1_175_000, 2, 2),
    ExpectedInitialClub("western_furies", "Western Furies", 1, 3_250_000, 2, 2),
    ExpectedInitialClub("selangor_royals", "Selangor Royals", 3, 5_000_000, 0, 0),
    ExpectedInitialClub("wellington_wardens", "Wellington Wardens", 3, 5_000_000, 0, 0),
)
