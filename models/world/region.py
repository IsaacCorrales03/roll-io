from dataclasses import dataclass, field
from uuid import UUID
from typing import List

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class Region:
    id: UUID
    name: str
    description: str

    climate: str
    locations: List[UUID] = field(default_factory=list)
    factions: List[UUID] = field(default_factory=list)

    state: StateBlock = field(default_factory=StateBlock)
    visibility: VisibilityRule = field(
        default_factory=lambda: VisibilityRule("hidden", [])
    )
