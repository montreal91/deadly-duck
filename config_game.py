
club_names = {
    1: [
        "Brisbane Rangers",
        "Canberra Masters",
        "Dandenong Pianists",
        "Melbourne Rockets",
        "Melbourne Slams",
        "Sydney Cangaroos",
        "Tasmanian Devils",
    ],
    2: [
        "Adelaide Thrashers",
        "Broome Witchers",
        "Darwin Ducks",
        "Mandurah Turtles",
        "Perth Penguins",
        "Rockingham Rocks",
        "Western Fury",
        # "Bunbury Pandas",
    ]
}

number_of_recent_matches = 5
sets_to_win = 2

# This number is for testing purposes, real should be much bigger
retirement_age = 31

class DdLeagueConfig:
    # This values should be even
    EXDIV_MATCHES = 2
    INDIV_MATCHES = 4
    DIV_CLUBS_IN_PLAYOFFS = 4 # This number should be power of two
    SETS_TO_WIN = 2
    MATCHES_TO_WIN = 4
    GAP_DAYS = 2
    SERIES_TOP_HOME_PATTERN = ( True, True, False, False, True, False, True )

class DdPlayerSkills:
    MEAN_VALUE = 5
    MAX_VALUE = 10
    STANDARD_DEVIATION = 2.5

    ENDURANCE_FACTOR = 2
    MIN_STAMINA_LOST = 1
    MAX_STAMINA_LOST = 3
    DAILY_RECOVERY_FACTOR = 0.2
    POSSIBLE_TALENTS = ( 1, 2, 4 )
    SKILL_PRECISION = 2

    SET_EXPERIENCE_FACTOR = 50


class DdRatingsParamerers:
    GROUND_LEVEL = 1
    MATCHES_COEFFICIENT = 2
    PRECISION = 2
    REGULAR_POINTS_FACTOR = 2.5
    ROUND_COEFFICIENT = 25
