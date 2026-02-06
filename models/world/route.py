from dataclasses import dataclass
from uuid import UUID

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class Route:
    id: UUID
    from_location: UUID
    to_location: UUID

    travel_time: str  # abstracto: "2d", "4h"
    danger: str       # low, medium, high
    mode: str         # road, sea, portal

    state: StateBlock = StateBlock()
    visibility: VisibilityRule = VisibilityRule("hidden", [])
