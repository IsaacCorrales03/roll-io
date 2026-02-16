from uuid import UUID
from typing import Dict
from .scene import Scene

class World:
    def __init__(self, id: UUID, name: str, lore: str, scenes: list | None = None):
        self.id = id
        self.name = name
        self.lore = lore
        self.scenes: list[Scene] = scenes if scenes is not None else []
        
    def add_scene(self, scene: Scene) -> None:
        if scene.world_id != self.id:
            raise ValueError("Scene does not belong to this world")

        self.scenes.append(scene)
