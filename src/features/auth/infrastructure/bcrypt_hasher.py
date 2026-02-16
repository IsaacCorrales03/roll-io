# auth/infrastructure/bcrypt_hasher.py
import bcrypt
from src.features.auth.ports.password_hasher import PasswordHasher

class BcryptPasswordHasher(PasswordHasher):

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
