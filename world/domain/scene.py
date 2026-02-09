from uuid import UUID, uuid4
from typing import Dict, List

from .section import Section
from models.base import Actor


class Scene:
    def __init__(self, id: UUID, name: str, map_url: str):
        self.id = id
        self.name = name
        self.map_url = map_url

        self.sections: Dict[str, Section] = {}
        self.actors: Dict[UUID, Actor] = {}

    def add_section(self, section: Section):
        self.sections[section.key] = section
