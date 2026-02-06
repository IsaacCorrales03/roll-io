from dataclasses import dataclass
from uuid import UUID

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class PointOfInterest:
    id: UUID
    name: str
    type: str  # shop, npc, object, trigger, secret
    location: UUID

    description: str = ""

    state: StateBlock = StateBlock()
    visibility: VisibilityRule = VisibilityRule("hidden", [])
