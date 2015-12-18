
from random import shuffle, randint


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
        self._days          = days
        self._divisions     = self._MakeDivisions(divisions)
        self._schedule      = []
        self._current_day   = 0

        if indiv_matches % 2 == 0:
            self._indiv_matches = indiv_matches
        else:
            self._indiv_matches = indiv_matches + 1

        if exdiv_matches % 2 == 0:
            self._exdiv_matches = exdiv_matches
        else:
            self._exdiv_matches = exdiv_matches + 1

    @property
    def teams(self):
        """
        Returns list of all teams in the league
        :rtype: list
        """
        res = []
        for div in self._divisions:
            res += list(div)
        return res

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
    def current_matches(self):
        res = []
        for item in self._schedule[self._current_day]:
            if type(item) != set:
                res.append(item)
        return res

    @property
    def days(self):
        return self._days

    def AddTeam(self, team_id=None):
        """
        Adds new team to the division with smallest number of teams
        :type team_id: int
        """
        assert team_id

        if team_id not in self.teams:
            div = min(self._divisions, key=len)
            div.add(team_id)

    def CreateSchedule(self):
        """
        Creates schedule for teams, if there are any.
        If there is no teams raises AssertionError
        """
        matches = self._CreateIntraDivMatches() + self._CreateExtraDivGames()
        self._schedule = [[set()] for i in range(self._days)]

        for match in matches:
            day = 0
            scheduled = False
            while not scheduled:
                if match[0] not in self._schedule[day][0] and match[1] not in self._schedule[day][0]:
                    self._schedule[day].append(match)
                    self._schedule[day][0].add(match[0])
                    self._schedule[day][0].add(match[1])
                    scheduled = True
                else:
                    day += 1
        shuffle(self._schedule)

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
        Creates list of matches played by teams in different divisions.
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
        Generates list of matches between teams in two different divisions.
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
        Creates list of games played by teams in the same divisions.
        :type division: list
        :type same_matches: int
        """
        res = []
        for team1 in division:
            for team2 in division:
                if team1 != team2:
                    res += [(team1, team2) for k in range(same_matches)]
        return res

    def QuickSimResult(self):
        home_score, away_score = 0, 0
        while home_score == away_score and max(home_score, away_score) != 2:
            home_score = randint(0, 2)
            away_score = randint(0, 2)
        return home_score, away_score

    def GetCurrentMatchByClubId(self, club_id):
        for match in self.current_matches:
            if club_id in match:
                return match
        return None

    def NextDay(self):
        self._current_day += 1
