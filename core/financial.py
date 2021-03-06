
"""
Created Jun 17, 2019

@author montreal91
"""

from typing import List
from typing import NamedTuple
from typing import Tuple


class DdTransaction(NamedTuple):
    """Named Tuple to store financial transaction data."""

    value: int
    comment: str

    def __repr__(self) -> str:
        return f"<[{id(self)}] {self.value} {self.comment:70}>"


class DdFinancialAccount:
    """
    Financial account.

    Balance can't become negative.
    """

    _transactions: List[DdTransaction]

    def __init__(self):
        self._transactions = []

    @property
    def balance(self):
        """Calculates balance of the account."""

        return sum(transaction.value for transaction in self._transactions)

    def GetLatestTransactions(self, n):
        """Returns n latest transactions.

        :param n: positive integer.
        """
        return self._transactions[-n:]

    def MergeTransactions(self, comment: str):
        """Merges all transactions in the account into one."""

        new_transaction = DdTransaction(value=self.balance, comment=comment)
        self._transactions = [new_transaction]

    def ProcessTransaction(self, transaction: DdTransaction) -> bool:
        """
        Processes one transaction.

        If transaction could not be processed, returns False.
        Otherwise returns True.
        """

        if transaction.value < 0 and abs(transaction.value) > self.balance:
            return False
        self._transactions.append(transaction)
        return True


class DdQuadraticContractCalculator:
    """
    Callable class that calculates player contract price based on level.

    Implements the quadratic growth of the contract price.
    """

    _coefficient: int

    def __call__(self, level: int) -> int:
        return self._coefficient * (level + 1) ** 2

    def __init__(self, coefficient: int):
        self._coefficient = coefficient


class DdStaticContractCalculator:
    """
    Callable class that calculates player contract price based on level.

    Contract prices are stored in special immutable list.
    """

    _prices: Tuple[int]

    def __call__(self, level: int) -> int:
        if level in range(len(self._prices)):
            return self._prices[level]
        return max(self._prices)

    def __init__(self, prices: List[int]):
        self._prices = tuple(prices)


class DdPracticeCalculator:
    """Callable class that calculates the cost of practice."""

    _coefficient: int

    def __call__(self, player_level: int, coach_level: int) -> int:
        return self._coefficient * player_level * coach_level ** 2

    def __init__(self, coefficient: int):
        self._coefficient = coefficient
