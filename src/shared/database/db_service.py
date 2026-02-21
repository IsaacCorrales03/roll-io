from typing import Optional
import mysql.connector
from src.shared.database.db_config import DB_DSN

class DatabaseService:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return self._conn.cursor(dictionary=dictionary)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def create_db_service() -> DatabaseService:
    conn = mysql.connector.connect(**DB_DSN)
    conn.autocommit = True  # type: ignore
    return DatabaseService(conn)