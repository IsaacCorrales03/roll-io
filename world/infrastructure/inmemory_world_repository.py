from uuid import UUID
from ..domain.world import World
from ..ports.world_repository import WorldRepository


class InMemoryWorldRepository(WorldRepository):
    def __init__(self):
        self._worlds: dict[UUID, World] = {}

    def save(self, world: World) -> None:
        self._worlds[world.id] = world

    def get(self, world_id: UUID) -> World | None:
        return self._worlds.get(world_id)
