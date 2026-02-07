# models/auth/auth_session.py
from uuid import UUID, uuid4
from datetime import datetime, timedelta


class AuthSession:
    def __init__(
        self,
        user_id: UUID,
        id: UUID | None = None,
        expires_at: datetime | None = None,
        revoked: bool = False,
        created_at: datetime | None = None,
    ):
        self.id = id or uuid4()
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (self.created_at + timedelta(days=7))
        self.revoked = revoked
