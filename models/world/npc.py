from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional

from .state import StateBlock

@dataclass
class NPC:
    id: UUID
    name: str
    role: str

    faction: Optional[UUID]
    current_location: UUID

    state: StateBlock = field(default_factory=StateBlock)
