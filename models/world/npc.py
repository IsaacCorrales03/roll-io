from dataclasses import dataclass
from uuid import UUID

from .state import StateBlock

@dataclass
class NPC:
    id: UUID
    name: str
    role: str

    faction: UUID | None
    current_location: UUID

    state: StateBlock = StateBlock()
