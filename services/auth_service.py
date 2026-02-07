from uuid import UUID
from datetime import datetime
from auth.ports.user_repository import UserRepository
from auth.ports.auth_session_repository import AuthSessionRepository
from auth.ports.password_hasher import PasswordHasher
from auth.domain.auth_session import AuthSession
from auth.domain.user import User
from uuid import uuid4

class AuthService:

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: AuthSessionRepository,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.password_hasher = password_hasher

    def login(self, email: str, password: str) -> AuthSession:
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Invalid credentials")

        session = AuthSession(user_id=user.id)
        self.session_repo.save(session)

        return session
    
    def register(self, username: str, email: str, password: str) -> User:
        if self.user_repo.exists_by_email(email):
            raise ValueError("El correo ya está registrado")

        password_hash = self.password_hasher.hash(password)
        user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hash,
            is_email_verified=False,
        )

        self.user_repo.save(user)
        return user

    # -----------------------
    # Funciones nuevas
    # -----------------------

    def get_session(self, session_id: str | UUID) -> AuthSession | None:
        """Devuelve la sesión activa a partir del session_id"""
        if isinstance(session_id, str):
            session_id = UUID(session_id)
        return self.session_repo.get(session_id)

    def get_user_by_id(self, user_id: str | UUID) -> User | None:
        """Devuelve el usuario por su ID"""
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.user_repo.get_by_id(user_id)
