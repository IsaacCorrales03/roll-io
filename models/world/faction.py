from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict

from .state import StateBlock

@dataclass
class Faction:
    id: UUID
    name: str
    description: str

    relations: Dict[UUID, str] = field(default_factory=dict)
    influence: Dict[str, int] = field(default_factory=dict)

    state: StateBlock = field(default_factory=StateBlock)
