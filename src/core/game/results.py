from dataclasses import dataclass
from typing import Any, List

from src.core.base import Actor


@dataclass
class QueryResult:
    """Resultado base de cualquier Query."""
    pass


@dataclass
class ArmorClassResult(QueryResult):
    value: int
    breakdown: List[dict]

@dataclass
class StatModifierResult(QueryResult):
    value: int
    breakdown: list[dict]

@dataclass
class GetActorsAtLocationResult(QueryResult):
    actors: list["Actor"] 

@dataclass
class ProficiencyBonusResult(QueryResult):
    value: int
    breakdown: list[dict]