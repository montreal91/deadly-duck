
club_names = {
    1: [
        "Canberra Masters",
        "Melbourne Slams",
        "Melbourne Rockets",
        # "Sydney Cangaroos",
        # "Brisbane Rangers",
        "Dandenong Pianists",
    ],
    2: [
        "Darwin Ducks",
        "Perth Penguins",
        "Adelaide Thrashers",
        "Broome Witchers",
        # "Mandurah Turtles",
        # "Bunbury Pandas",
    ]
}

number_of_recent_matches = 5
sets_to_win = 2

# This number is for testing purposes, real should be much bigger
retirement_age = 22

# This values should be even
class DdLeagueConfig:
    INDIV_MATCHES = 2
    EXDIV_MATCHES = 2

class DdPlayerSkills:
    MEAN_VALUE = 5
    MAX_VALUE = 10
    STANDARD_DEVIATION = 2.5
    ENDURANCE_FACTOR = 10
    MIN_STAMINA_LOST = 1
    MAX_STAMINA_LOST = 3
    DAILY_RECOVERY_FACTOR = 0.25
