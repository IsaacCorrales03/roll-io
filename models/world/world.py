from dataclasses import dataclass, field
from uuid import UUID
from typing import List

from .state import StateBlock
from .common import Metadata

@dataclass
class World:
    id: UUID
    name: str
    description: str

    regions: List[UUID] = field(default_factory=list)
    timelines: List[UUID] = field(default_factory=list)

    global_state: StateBlock = field(default_factory=StateBlock)
    metadata: Metadata = field(default_factory=lambda: Metadata({}, {}))
