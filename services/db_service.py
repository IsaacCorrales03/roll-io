import mysql.connector
from services.db_config import DB_DSN


class DatabaseService:
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_DSN)

    def cursor(self, dictionary=False):
        return self.conn.cursor(dictionary=dictionary)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
