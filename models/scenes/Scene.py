from dataclasses import dataclass
from uuid import UUID
from typing import Dict, List
from .SceneActor import SceneActor
from .Section import Section

@dataclass
class Scene:
    id: UUID
    name: str
    map_url: str
    sections: Dict[str, Section]          # a1 -> Section
    actors: Dict[UUID, SceneActor]        # actor_id -> SceneActor
