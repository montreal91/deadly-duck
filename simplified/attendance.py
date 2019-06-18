
"""
Created Jun 18, 2019

@author montreal91

Attendance-related stuff.
"""

from typing import Any
from typing import Dict
from typing import NamedTuple


class DdCourt:
    """A class to incapsulate court-related objects."""

    # `_capacity` and `_rent_cost` are 'Final' values. Once initialized they do
    # not change.
    _capacity: int
    _rent_cost: int

    _ticket_price: int

    def __init__(self, capacity, rent_cost):
        self._capacity = capacity
        self._rent_cost = rent_cost

        self._ticket_price = 0

    @property
    def capacity(self) -> int:
        """Court's capacity."""

        return self._capacity

    @property
    def json(self) -> Dict[str, Any]:
        """Json-serialazable representation of the class."""

        return dict(
            capacity=self.capacity,
            rent_cost=self.rent_cost,
            ticket_price=self.ticket_price,
        )

    @property
    def rent_cost(self) -> int:
        """
        Court's rent cost.

        In other words, amout of money require to rent this court.
        """
        return self._rent_cost

    @property
    def ticket_price(self) -> int:
        """Ticket price on this court."""

        return self._ticket_price

    @ticket_price.setter
    def ticket_price(self, value: int):
        """Sets ticket price on this court."""

        self._ticket_price = value

    def GetMatchIncome(self, attendance: int) -> int:
        """Calculates match income held on this court with given attendance."""

        actual_attendance = max(min(attendance, self._capacity), 0)
        return actual_attendance * self._ticket_price


class DdAttendanceCalculator:
    """A simple class to calculate match attendance."""

    def __call__(
        self,
        ticket_price: int,
        home_fame: int,
        away_fame: int,
        reputation: int,
        match_importance: int
    ) -> int:
        arguments = (
            ticket_price, home_fame, away_fame, reputation, match_importance
        )
        asdfg = zip(self._coefficients, arguments, self._powers)
        import ipdb
        if ticket_price > 0:
            ipdb.set_trace()
        return int(sum(k * x ** y for k, x, y in asdfg))

    def __init__(
        self,
        price: float,
        home_fame: float,
        away_fame: float,
        reputation: float,
        importance: float,
        hard: bool
    ):
        self._coefficients = (
            price, home_fame, away_fame, reputation, importance
        )
        self._is_hard = hard

    @property
    def _powers(self):
        res = [1 for _ in range(len(self._coefficients))]
        if self._is_hard:
            res[0] = 2
        return tuple(res)

class DdAttendanceParams(NamedTuple):
    """Passive class to store attendance parameters."""

    price: float
    home_fame: float
    away_fame: float
    reputation: float
    importance: float
