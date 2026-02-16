from uuid import UUID
from typing import List
from .section import Section


class Scene:
    def __init__(
        self,
        id: UUID,
        world_id: UUID,
        name: str,
        map_url: str,
        description: str = ""
    ):
        self.id = id
        self.world_id = world_id
        self.name = name
        self.map_url = map_url
        self.description = description

        self._sections: List[Section] = []

    # -------------------------
    # Section Management
    # -------------------------

    @property
    def sections(self) -> List[Section]:
        return list(self._sections)


    def add_section(self, section: Section):
        if section.scene_id != self.id:
            raise ValueError("Section does not belong to this scene")

        if self.get_section(section.id):
            raise ValueError("Section already exists in scene")

        self._sections.append(section)


    def get_section(self, section_id: UUID) -> Section | None:
        return next((s for s in self._sections if s.id == section_id), None)
