from uuid import UUID

from flask import session
from src.features.auth.domain.auth_session import AuthSession
from src.features.auth.ports.auth_session_repository import AuthSessionRepository
from src.shared.database.db_service import DatabaseService


class MySQLAuthSessionRepository(AuthSessionRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    def save(self, session: AuthSession) -> None:
        cur = self.db.cursor()

        cur.execute(
            """
            INSERT INTO auth_sessions (id, user_id, expires_at, revoked)
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(session.id),
                str(session.user_id),
                session.expires_at,
                session.revoked,
            )
        )
        self.db.commit()
        

    def get(self, session_id: UUID) -> AuthSession | None:
        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM auth_sessions WHERE id = %s LIMIT 1",
            (str(session_id),)
        )
        row: dict | None = cur.fetchone()  # type: ignore
        if not row:
            return None
        return AuthSession(
            id=UUID(str(row["id"])),
            user_id=UUID(str(row["user_id"])),
            expires_at=row["expires_at"],
            revoked=bool(row["revoked"]),
        )


    def revoke(self, session_id: UUID) -> None:
        raise NotImplementedError

