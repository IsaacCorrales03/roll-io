from uuid import UUID, uuid4
from typing import Dict

from .scene import Scene


class World:
    def __init__(self, id: UUID, name: str, lore: str = "", description: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.lore = lore
        self.scenes: Dict[UUID, Scene] = {}

    def add_scene(self, scene: Scene):
        self.scenes[scene.id] = scene
