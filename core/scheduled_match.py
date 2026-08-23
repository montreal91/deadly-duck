"""
Created Aug 22, 2026

@author montreal91
"""
from uuid import uuid4


class ScheduledMatch:
    """Passive class for a scheduled match."""

    def __init__(
            self,
            home_pk,
            away_pk,
            match_id=None,
            playoff_series_id=None,
    ):
        self.match_id = match_id or str(uuid4())
        self.home_pk = home_pk
        self.away_pk = away_pk
        self.playoff_series_id = playoff_series_id
        self.is_played = False

    def __repr__(self):
        return f"<{self.match_id}: {self.home_pk} - {self.away_pk}>"
