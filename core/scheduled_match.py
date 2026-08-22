"""
Created Aug 22, 2026

@author montreal91
"""

class ScheduledMatch:
    """Passive class for a scheduled match."""

    def __init__(self, home_pk, away_pk):
        self.home_pk = home_pk
        self.away_pk = away_pk
        self.is_played = False

    def __repr__(self):
        return f"<{self.home_pk} - {self.away_pk}>"
