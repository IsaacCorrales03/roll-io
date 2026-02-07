from dataclasses import dataclass, field
from uuid import UUID

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class PointOfInterest:
    id: UUID
    name: str
    type: str
    location: UUID

    description: str = ""

    state: StateBlock = field(default_factory=StateBlock)
    visibility: VisibilityRule = field(
        default_factory=lambda: VisibilityRule("hidden", [])
    )
