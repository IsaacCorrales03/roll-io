# auth/ports/auth_session_repository.py
from abc import ABC, abstractmethod
from uuid import UUID
from src.features.auth.domain.auth_session import AuthSession


class AuthSessionRepository(ABC):

    @abstractmethod
    def save(self, session: AuthSession) -> None: ...

    @abstractmethod
    def get(self, session_id: UUID) -> AuthSession | None: ...

    @abstractmethod
    def revoke(self, session_id: UUID) -> None: ...
