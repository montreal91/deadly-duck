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
    ExpectedInitialClub("farm_club_0", "Farm Club 0", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_1", "Farm Club 1", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_2", "Farm Club 2", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_3", "Farm Club 3", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_4", "Farm Club 4", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_5", "Farm Club 5", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_6", "Farm Club 6", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_7", "Farm Club 7", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_8", "Farm Club 8", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_9", "Farm Club 9", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_10", "Farm Club 10", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_11", "Farm Club 11", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_12", "Farm Club 12", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_13", "Farm Club 13", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_14", "Farm Club 14", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_15", "Farm Club 15", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_16", "Farm Club 16", 0, 0, 0, 0),
    ExpectedInitialClub("farm_club_17", "Farm Club 17", 0, 0, 0, 0),
)
