"""
Created September 22, 2026

@author montreal91
"""
from dataclasses import dataclass
from dataclasses import field
from typing import List

from core.contract import Contract


@dataclass(frozen=True)
class UpdateResult:
    success: bool
    reason: str
    new_contracts: List[Contract] = field(default_factory=list)
    new_assignments: List[int] = field(default_factory=list)
