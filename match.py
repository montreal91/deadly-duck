
class JMatch(object):
    def __init__(self, home_team_id=None, away_team_id=None, day=0):
        super(JMatch, self).__init__()
        self._home_team_id = home_team_id
        self._away_team_id = away_team_id
        self._day = day

        self._home_team_points = 0
        self._away_team_points = 0
        self._is_played = False

    @property
    def home_team(self):
        return self._home_team_id

    @home_team.setter
    def home_team(self, team_id):
        self._home_team_id = team_id

    @property
    def away_team(self):
        return self._away_team_id

    @away_team.setter
    def away_team(self, team_id):
        assert isinstance( team_id, int )
        self._away_team_id = team_id

    @property
    def score(self):
        return self._home_team_points, self._away_team_points

    @score.setter
    def score(self, result):
        self._home_team_points = result[0]
        self._away_team_points = result[1]
        self._is_played = True

    @property
    def day(self):
        return self._day

    @day.setter
    def day(self, val):
        assert isinstance( val, int )
        self._day = val

    @property
    def is_played(self):
        return  self._is_played

    def SetMatchPlayed(self):
        self._is_played = True

    def __str__(self):
        return "<{0:d}> vs <{1:d}>".format(self._home_team_id, self._away_team_id)

    def __repr__(self):
        return "JMatch <{0:d}> vs <{1:d}> on {2:d}".format(self._home_team_id, self._away_team_id, self._day)