from abc import ABC, abstractmethod
from uuid import UUID
from ..domain.world import World

class WorldRepository(ABC):

    @abstractmethod
    def save(self, world: World) -> None: ...


    @abstractmethod
    def get_by_id(self, world_id: UUID) -> World | None: ...