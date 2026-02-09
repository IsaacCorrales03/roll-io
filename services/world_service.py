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
    ) -> World:

        world = World(
            id=uuid4(),
            name=name,
            lore=lore,
        )

        scene = Scene(
            id=uuid4(),
            name=initial_scene_name,
            map_url=initial_scene_map_url,
        )

        # Sección mínima obligatoria
        scene.add_section(
            Section(
                key="a1",
                fog=True
            )
        )

        world.add_scene(scene)

        self.repo.save(world)

        return world

