from datetime import datetime
from uuid import UUID
from src.features.auth.ports.session_validator import SessionValidator
from src.features.auth.ports.auth_session_repository import AuthSessionRepository


class DBSessionValidator(SessionValidator):

    def __init__(self, session_repo: AuthSessionRepository):
        self.session_repo = session_repo

    def validate(self, session_id: UUID) -> UUID | None:
        session = self.session_repo.get(session_id)
        if not session:
            return None

        if session.revoked:
            return None

        if session.expires_at < datetime.utcnow():
            return None

        return session.user_id
