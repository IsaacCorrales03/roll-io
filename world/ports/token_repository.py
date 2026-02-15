from abc import ABC, abstractmethod
from uuid import UUID


class TokenRepository(ABC):

    @abstractmethod
    def create(self, token_data: dict) -> None:
        pass

    @abstractmethod
    def get_by_id(self, token_id: UUID | str) -> dict | None:
        pass

    @abstractmethod
    def get_by_character(self, character_id: UUID | str) -> dict | None:
        pass

    @abstractmethod
    def update_position(self, token_id: UUID | str, x: int, y: int) -> None:
        pass

    @abstractmethod
    def delete(self, token_id: UUID | str) -> None:
        pass
