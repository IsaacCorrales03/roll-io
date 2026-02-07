# models/auth/user.py
from uuid import UUID, uuid4
from datetime import datetime


class User:
    def __init__(
        self,
        username: str,
        email: str,
        password_hash: str,
        id: UUID | None = None,
        is_email_verified: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id or uuid4()
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_email_verified = is_email_verified
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
