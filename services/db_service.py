from typing import Optional


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
    import mysql.connector
    from services.db_config import DB_DSN

    conn = mysql.connector.connect(**DB_DSN)
    return DatabaseService(conn)
