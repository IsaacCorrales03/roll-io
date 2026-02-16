from uuid import UUID
from src.shared.database.db_service import DatabaseService
from ..ports.token_repository import TokenRepository


class MySQLTokenRepository(TokenRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    # -------------------------
    # CREATE
    # -------------------------
    def create(self, token_data: dict) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO tokens (
                id,
                character_id,
                x,
                y,
                size_x,
                size_y,
                fallback_color,
                owner_user_id,
                is_visible,
                label
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                token_data["id"],
                token_data["character_id"],
                token_data["x"],
                token_data["y"],
                token_data.get("size_x", 1),
                token_data.get("size_y", 1),
                token_data.get("fallback_color", "#ff0000"),
                token_data.get("owner_user_id"),
                token_data.get("is_visible", True),
                token_data.get("label", ""),
            )
        )
        self.db.commit()

    # -------------------------
    # GET BY ID
    # -------------------------
    def get_by_id(self, token_id: UUID | str) -> dict | None:
        if isinstance(token_id, UUID):
            token_id = str(token_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM tokens WHERE id = %s LIMIT 1",
            (token_id,)
        )
        return cur.fetchone()

    # -------------------------
    # GET BY CHARACTER
    # -------------------------
    def get_by_character(self, character_id: UUID | str) -> dict | None:
        if isinstance(character_id, UUID):
            character_id = str(character_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                t.*,
                c.token_texture
            FROM tokens t
            JOIN characters c ON c.id = t.character_id
            WHERE t.character_id = %s
            LIMIT 1
        """, (character_id,))

        return cur.fetchone()

    # -------------------------
    # UPDATE POSITION
    # -------------------------
    def update_position(self, token_id: UUID | str, x: int, y: int) -> None:
        if isinstance(token_id, UUID):
            token_id = str(token_id)

        cur = self.db.cursor()
        cur.execute(
            """
            UPDATE tokens
            SET x = %s, y = %s
            WHERE id = %s
            """,
            (x, y, token_id)
        )
        self.db.commit()

    # -------------------------
    # DELETE
    # -------------------------
    def delete(self, token_id: UUID | str) -> None:
        if isinstance(token_id, UUID):
            token_id = str(token_id)

        cur = self.db.cursor()
        cur.execute(
            "DELETE FROM tokens WHERE id = %s",
            (token_id,)
        )
        self.db.commit()
