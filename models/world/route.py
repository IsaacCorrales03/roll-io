from dataclasses import dataclass, field
from uuid import UUID

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class Route:
    id: UUID
    from_location: UUID
    to_location: UUID

    travel_time: str
    danger: str
    mode: str

    state: StateBlock = field(default_factory=StateBlock)
    visibility: VisibilityRule = field(
        default_factory=lambda: VisibilityRule("hidden", [])
    )
