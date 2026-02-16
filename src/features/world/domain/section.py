# sections/domain/section.py

from uuid import UUID
from dataclasses import dataclass

@dataclass
class Section:
    id: UUID
    scene_id: UUID
    name: str
    texture_url: str
    offset_x: int
    offset_y: int
    width_px: int
    height_px: int
    tile_size: int
    grid_type: str = "square"

    @property
    def cols(self) -> int:
        return self.width_px // self.tile_size

    @property
    def rows(self) -> int:
        return self.height_px // self.tile_size

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "scene_id": str(self.scene_id),
            "name": self.name,
            "texture_url": self.texture_url,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "tile_size": self.tile_size,
            "grid_type": self.grid_type,
        }

    @staticmethod
    def from_dict(data: dict) -> "Section":
        from uuid import UUID
        return Section(
            id=UUID(data["id"]),
            scene_id=UUID(data["scene_id"]),
            name=data["name"],
            texture_url=data["texture_url"],
            offset_x=data["offset_x"],
            offset_y=data["offset_y"],
            width_px=data["width_px"],
            height_px=data["height_px"],
            tile_size=data["tile_size"],
            grid_type=data["grid_type"],
        )
