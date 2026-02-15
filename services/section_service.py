# sections/application/section_service.py

import uuid
from world.domain.section import Section
from world.ports.section_repository import SectionRepository

class SectionService:

    def __init__(self, repo: SectionRepository):
        self.repo = repo

    def create(
        self,
        scene_id: uuid.UUID,
        name: str,
        texture_url: str,
        offset_x: int,
        offset_y: int,
        width_px: int,
        height_px: int,
        tile_size: int,
        grid_type: str = "square",
    ) -> Section:

        section = Section(
            id=uuid.uuid4(),
            scene_id=scene_id,
            name=name,
            texture_url=texture_url,
            offset_x=offset_x,
            offset_y=offset_y,
            width_px=width_px,
            height_px=height_px,
            tile_size=tile_size,
            grid_type=grid_type,
        )

        self.repo.create(section.to_dict())
        return section

    def get_by_scene(self, scene_id: uuid.UUID):
        return self.repo.get_by_scene(scene_id)
