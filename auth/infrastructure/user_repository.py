from uuid import UUID
from datetime import datetime
from auth.domain.user import User
from auth.ports.user_repository import UserRepository
from services.db_service import DatabaseService


class MySQLUserRepository(UserRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    def exists_by_email(self, email: str) -> bool:
        cur = self.db.cursor(dictionary=True)
        cur.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1", (email,))
        return cur.fetchone() is not None
    
    def get_by_email(self, email: str) -> User | None:
        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE email = %s LIMIT 1",
            (email,)
        )
        row = cur.fetchone()
        if not isinstance(row, dict) or not row:
            return None
        return self._row_to_user(row)

    def get_by_id(self, user_id: UUID | str) -> User | None:
        """Nuevo método: devuelve usuario por UUID"""
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE id = %s LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        if not isinstance(row, dict) or not row:
            return None
        return self._row_to_user(row)

    def save(self, user: User) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO users (id, username, email, password_hash, is_email_verified)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(user.id),
                user.username,
                user.email,
                user.password_hash,
                user.is_email_verified,
            )
        )
        self.db.commit()

    # -----------------------------
    # Método privado auxiliar
    # -----------------------------
    def _row_to_user(self, row: dict) -> User:
        """Convierte fila de DB a objeto User"""
        return User(
            id=UUID(str(row["id"])),
            username=str(row["username"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
            is_email_verified=bool(row["is_email_verified"]),
            created_at=datetime.fromisoformat(str(row["created_at"])) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(str(row["updated_at"])) if row.get("updated_at") else None,
        )
