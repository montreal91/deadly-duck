import sqlite3

from random import shuffle, choice

from match  import JMatch
from club   import JClub


class JLeague(object):
    """docstring for JLeague"""

    def __init__(self, divisions=1, indiv_matches=2, exdiv_matches=2, days=12):
        """
        Constructor for JLeague
        :type divisions: int
        :type indiv_matches: int
        :type exdiv_matches: int
        :type days: int
        """
        super(JLeague, self).__init__()
        self._days              = days
        self._divisions         = self._MakeDivisions(divisions)
        self._schedule          = []
        self._current_day       = 0
        self._current_season    = 1
        self._total_matches     = 0

        if indiv_matches % 2 == 0:
            self._indiv_matches = indiv_matches
        else:
            self._indiv_matches = indiv_matches + 1

        if exdiv_matches % 2 == 0:
            self._exdiv_matches = exdiv_matches
        else:
            self._exdiv_matches = exdiv_matches + 1

        self._conn = sqlite3.connect("testing.db")
        self._curs = self._conn.cursor()
        self._DropAllTables()
        self._CreateNewTables()

    @property
    def clubs( self ):
        """
        Returns list of all clubs in the league
        :rtype: list
        """
        res = set()
        for div in self._divisions:
            for club in div:
                res.add(club.club_id)
        return res

    def _DropAllTables(self):
        try:
            self._curs.execute("DROP TABLE clubs")
            self._curs.execute("DROP TABLE matches")
        except sqlite3.OperationalError:
            print("There were no tables")

    def _CreateNewTables(self):
        self._curs.execute(
            """
            CREATE TABLE clubs (
                n_club_id INTEGER PRIMARY KEY,
                c_club_name TEXT NOT NULL,
                b_playable BOOL NOT NULL
            );
            """
        )
        self._curs.execute(
            """
            CREATE TABLE matches (
                n_match_id INTEGER PRIMARY KEY,
                n_home_team INTEGER,
                n_away_team INTEGER,
                n_home_team_pts INTEGER NOT NULL,
                n_away_team_pts INTEGER NOT NULL,
                n_day INTEGER NOT NULL,
                n_season INTEGER NOT NULL,
                b_is_played BOOL NOT NULL,
                FOREIGN KEY (n_home_team) REFERENCES clubs(n_club_id),
                FOREIGN KEY (n_away_team) REFERENCES clubs(n_club_id)
            )
            """
        )

    def _MakeDivisions(self, divisions):
        """
        Creates empty divisions.
        :type divisions: int
        :rtype: list
        """
        if divisions < 1:
            raise Exception("There should be at least one division in the league")
        else:
            return [set() for i in range(divisions)]

    @property
    def current_day(self):
        return  self._current_day

    @property
    def current_season(self):
        return self._current_season

    @property
    def current_matches(self):
        res = []
        for item in self._schedule[self._current_day]:
            if type(item) != set:
                res.append(item)
        return res

    @property
    def days(self):
        return self._days

    def AddClub( self, club=None ):
        """
        Adds new team to the division with smallest number of clubs
        :type club: JClub
        """
        assert club

        if club.club_id not in self.clubs:
            div = min(self._divisions, key=len)
            div.add( club )
            query = "INSERT INTO clubs VALUES({0:d}, '{1:s}', {2:d});".format(
                club.club_id, club.name, int(club.playable)
            )
            self._curs.execute(query)


    def CreateSchedule(self):
        """
        Creates schedule for clubs, if there are any.
        If there is no clubs raises AssertionError
        """
        matches = self._CreateIntraDivMatches() + self._CreateExtraDivGames()
        self._schedule = [[set()] for i in range(self._days)]

        for match in matches:
            self._total_matches += 1
            day = 0
            scheduled = False
            while not scheduled:
                if match[0] not in self._schedule[day][0] and match[1] not in self._schedule[day][0]:
                    match_entry = JMatch(
                        match_id=self._total_matches,
                        home_team_id=match[0].club_id,
                        away_team_id=match[1].club_id
                    )
                    self._schedule[day].append(match_entry)
                    self._schedule[day][0].add(match[0])
                    self._schedule[day][0].add(match[1])
                    scheduled = True
                else:
                    day += 1
        shuffle(self._schedule)
        for day in range(len(self._schedule)):
            for something in self._schedule[day]:
                if isinstance(something, set):
                    continue
                something.day = day


    def _CreateIntraDivMatches(self):
        """
        Generates list of matches inside all divisions.
        :rtype: list
        """
        matches_l = []
        same_matches = int(self._indiv_matches / 2)
        for division in self._divisions:
            matches_l += self._MakeMatchesInsideDivision(division, same_matches)
        return matches_l

    def _CreateExtraDivGames(self):
        """
        Creates list of matches played by clubs in different divisions.
        :rtype: list
        """
        matches_l = []
        same_matches = self._exdiv_matches / 2
        for div1 in self._divisions:
            for div2 in self._divisions:
                if div1 != div2:
                    matches_l += self._MakeMatchesBetweenDivisions( div1, div2, same_matches)
        return matches_l

    def _MakeMatchesBetweenDivisions(self, div1, div2, same_matches):
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
                res += [(team1, team2) for k in range(same_matches)]
        return res

    def _MakeMatchesInsideDivision(self, division, same_matches):
        """
        Creates list of games played by clubs in the same divisions.
        :type division: list
        :type same_matches: int
        """
        res = []
        for team1 in division:
            for team2 in division:
                if team1 != team2:
                    res += [(team1, team2) for k in range(same_matches)]
        return res

    # Simple method for testing purposes
    def QuickSimResult(self):
        possible_outcomes = [(2, 0), (2, 1), (0, 2), (1, 2)]
        return choice(possible_outcomes)

    def GetCurrentMatchByClubId(self, club_id):
        for match in self.current_matches:
            if club_id == match.home_team or club_id == match.away_team:
                return match
        return None

    def GetClubById(self, club_id):
        if not club_id in self.clubs:
            return None

        for division in self._divisions:
            for club in division:
                if club.club_id == club_id:
                    return club

    def _SetPlayersForUnplayableClubs(self):
        for div in self._divisions:
            for club in div:
                if not club.playable:
                    club.SetRandomPlayer()

    def NextDay(self):
        self._current_day += 1
        for div in self._divisions:
            for club in div:
                club.Deselect()

    def PlayCurrentMatches(self):
        for match in self.current_matches:
            match.score = self.QuickSimResult()
            match.SetMatchPlayed()
            query = """
                INSERT INTO matches VALUES({0:d}, {1:d}, {2:d}, {3:d}, {4:d}, {5:d}, {6:d}, {7:d});
            """.format(
                match.match_id,
                match.home_team,
                match.away_team,
                match.score[0],
                match.score[1],
                match.day,
                self._current_season,
                int(match.is_played)
            )
            self._curs.execute(query)

    def GetCurrentStandings(self):
        query = """
        SELECT clubs.b_playable, clubs.c_club_name, sum(CASE
                WHEN clubs.n_club_id = matches.n_home_team THEN matches.n_home_team_pts
                WHEN clubs.n_club_id = matches.n_away_team THEN matches.n_away_team_pts
                ELSE 0
            END) AS points
        FROM clubs, matches
        WHERE matches.n_season = {0:d}
        GROUP BY clubs.c_club_name
        ORDER BY points DESC
        """.format(self._current_season)
        res = self._curs.execute(query)
        return res.fetchall()

    def ProceedToNextSeason(self):
        self._current_season += 1
        self._current_day = 0
        self.CreateSchedule()
