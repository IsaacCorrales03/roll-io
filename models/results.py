from dataclasses import dataclass
from typing import Any, List


@dataclass
class QueryResult:
    """Resultado base de cualquier Query."""
    pass


@dataclass
class ArmorClassResult(QueryResult):
    value: int
    breakdown: List[dict]