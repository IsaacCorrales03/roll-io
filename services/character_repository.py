import uuid
from typing import Optional, Dict, Any, cast
from services.db_service import create_db_service


class CharacterRepository:
    def __init__(self):
        self.db = create_db_service()
        self._create_table()

    def _create_table(self):
        with self.db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id CHAR(36) PRIMARY KEY,
                    owner_id CHAR(36) NOT NULL,
                    name VARCHAR(64) NOT NULL,

                    race_key VARCHAR(32) NOT NULL,
                    class_key VARCHAR(32) NOT NULL,

                    level INT NOT NULL DEFAULT 1,   

                    strength INT NOT NULL,
                    dexterity INT NOT NULL,
                    constitution INT NOT NULL,
                    intelligence INT NOT NULL,
                    wisdom INT NOT NULL,
                    charisma INT NOT NULL,

                    hp INT NOT NULL,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

                    CONSTRAINT fk_owner FOREIGN KEY (owner_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """)
        self.db.commit()

    def create(self, character, owner_id: uuid.UUID) -> str:
        with self.db.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO characters (
                        id, owner_id, name, race_key, class_key,
                        level,
                        strength, dexterity, constitution,
                        intelligence, wisdom, charisma,
                        hp
                    ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(character["id"]),
                    str(owner_id),
                    character["name"],
                    character["race"]["key"],
                    character["class"]["name"],
                    character["level"],
                    character["attributes"]["STR"],
                    character["attributes"]["DEX"],
                    character["attributes"]["CON"],
                    character["attributes"]["INT"],
                    character["attributes"]["WIS"],
                    character["attributes"]["CHA"],
                    character["hp"]["max"]
                ))
            except Exception as e:
                print("Error al crear personaje:", e)

        self.db.commit()
        return character["id"]

    def get_by_id(self, character_id: str) -> Optional[Dict[str, Any]]:
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM characters WHERE id = %s",
                (character_id,)
            )
            return cast(Optional[Dict[str, Any]], cursor.fetchone())

    def get_by_owner(self, owner_id: str) -> list[Dict[str, Any]]:
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM characters WHERE owner_id = %s",
                (owner_id,)
            )
            return cast(list[Dict[str, Any]], cursor.fetchall())

    def delete(self, character_id: str) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM characters WHERE id = %s",
                (character_id,)
            )
            deleted = cursor.rowcount > 0

        self.db.commit()
        return deleted
