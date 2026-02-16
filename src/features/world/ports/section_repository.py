# sections/ports/section_repository.py

from abc import ABC, abstractmethod
from uuid import UUID

class SectionRepository(ABC):

    @abstractmethod
    def create(self, section_data: dict) -> None: ...

    @abstractmethod
    def get_by_id(self, section_id: UUID | str) -> dict | None: ...

    @abstractmethod
    def get_by_scene(self, scene_id: UUID | str) -> list[dict]: ...

    @abstractmethod
    def delete(self, section_id: UUID | str) -> None: ...
