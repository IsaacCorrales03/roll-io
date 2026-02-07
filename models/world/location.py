from dataclasses import dataclass, field
from uuid import UUID
from typing import List, Optional

from .state import StateBlock
from .visibility import VisibilityRule

@dataclass
class Location:
    id: UUID
    name: str
    type: str  # city, dungeon, wilderness, interior, etc.

    region: UUID
    parent: Optional[UUID] = None
    children: List[UUID] = field(default_factory=list)

    description: str = ""
    points_of_interest: List[UUID] = field(default_factory=list)
    routes: List[UUID] = field(default_factory=list)

    state: StateBlock = field(default_factory=StateBlock)
    visibility: VisibilityRule = field(
        default_factory=lambda: VisibilityRule("hidden", [])
    )

    def reveal(self):
        """Make this location visible."""
        self.visibility = VisibilityRule("visible", [])