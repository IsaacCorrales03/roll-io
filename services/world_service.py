from uuid import uuid4
from world.domain.world import World
from world.domain.scene import Scene
from world.domain.section import Section
from world.ports.world_repository import WorldRepository

class WorldService:
    def __init__(self, repo: WorldRepository):
        self.repo = repo

    def create_world(
        self,
        name: str,
        lore: str,
        initial_scene_name: str,
        initial_scene_map_url: str,
        initial_scene_description: str,
        sections_data: list[dict],
    ) -> World:

        if not name:
            raise ValueError("World name is required")

        world = World(
            id=uuid4(),
            name=name,
            lore=lore,
        )

        scene = Scene(
            id=uuid4(),
            world_id=world.id,
            name=initial_scene_name,
            map_url=initial_scene_map_url,
            description=initial_scene_description,
        )

        # Crear secciones
        for s in sections_data:
            section = Section(
                id=uuid4(),
                scene_id=scene.id,
                name=s.get("name", ""),
                offset_x=s["offset_x"],
                offset_y=s["offset_y"],
                width_px=s["width_px"],
                height_px=s["height_px"],
                tile_size=s["tile_size"],
                grid_type=s.get("grid_type", "square"),
                texture_url=s["texture_url"],
            )
            scene.add_section(section)

        world.add_scene(scene)

        self.repo.save(world)

        return world
