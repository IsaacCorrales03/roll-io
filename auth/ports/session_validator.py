# auth/ports/session_validator.py
from abc import ABC, abstractmethod
from uuid import UUID


class SessionValidator(ABC):
    @abstractmethod
    def validate(sel, session_id: UUID) -> UUID | None:
        """Devuelve user_id o None"""
        return 