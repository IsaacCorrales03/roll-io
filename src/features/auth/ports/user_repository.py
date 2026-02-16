# auth/ports/user_repository.py
from abc import ABC, abstractmethod
from src.features.auth.domain.user import User
from uuid import UUID

class UserRepository(ABC):

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> None: ...
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None: ...