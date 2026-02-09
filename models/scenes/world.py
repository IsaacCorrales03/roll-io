from dataclasses import dataclass
from uuid import UUID  
from typing import Dict, List
from .Scene import Scene

@dataclass
class World:
    id: UUID
    name: str
    description: str
    scenes: Dict[UUID, Scene]
