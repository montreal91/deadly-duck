
from random import choice


class JClub(object):
    def __init__(self, club_id=None, name=None, playable=False):
        super(JClub, self).__init__()
        self._club_id = club_id
        self._name = name
        self._players = set()
        self._playable = playable
        self._selected_player = None

    @property
    def club_id(self):
        return self._club_id

    @property
    def name(self):
        return self._name

    @property
    def number_of_players(self):
        return len(self._players)

    @property
    def playable(self):
        return self._playable

    @property
    def players(self):
        return list(self._players)

    @property
    def selected_player(self):
        return self._selected_player

    def RenameClub(self, new_name):
        assert isinstance( new_name, str )
        self._name = new_name

    def AddPlayer(self, player_id):
        self._players.add(player_id)

    def RemovePlayer(self, player_id):
        self._players.remove(player_id)

    def SelectPlayerById(self, player_id):
        assert player_id in self._players
        self._selected_player = player_id

    def SelectRandomPlayer(self):
        self._selected_player = choice(self.players)

    def Deselect(self):
        self._selected_player = None

    def __repr__(self):
        return "#{0:d}: %s".format(self._club_id, self._name)