import traceback
import uuid
from typing import Optional, Dict, Any, cast
from src.shared.database.db_service import create_db_service


class CharacterRepository:
    def __init__(self):
        self.db = create_db_service()

    def create(self, character, owner_id: uuid.UUID, texture = None) -> str:
        with self.db.cursor() as cursor:
            if not texture:
                defalut_token = f"/imgs/{character['class']['name']}.jpg"
            else:
                defalut_token = texture
            try:
                cursor.execute("""
                    INSERT INTO characters (
                        id, owner_id, name, race_key, class_key,
                        level,
                        strength, dexterity, constitution,
                        intelligence, wisdom, charisma,
                        hp, max_hp, token_texture
                    ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    character["hp"]["current"],
                    character["hp"]["max"],
                    defalut_token
                ))
            except Exception as e:
                import traceback
                traceback.print_exc()

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
    
    def save(self, character: Dict[str, Any], owner_id: uuid.UUID) -> str:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM characters WHERE id = %s",
                (character["id"],)
            )
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE characters SET
                        name = %s,
                        race_key = %s,
                        class_key = %s,
                        level = %s,
                        strength = %s,
                        dexterity = %s,
                        constitution = %s,
                        intelligence = %s,
                        wisdom = %s,
                        charisma = %s,
                        hp = %s,
                        max_hp = %s,
                        owner_id = %s,
                        token_texture = %s

                    WHERE id = %s
                """, (
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
                    character["hp"]["current"],
                    character["hp"]["max"],
                    str(owner_id),
                    character["id"],
                    character["token_texture"]
                ))
            else:
                cursor.execute("""
                    INSERT INTO characters (
                        id, owner_id, name, race_key, class_key,
                        level,
                        strength, dexterity, constitution,
                        intelligence, wisdom, charisma,
                        hp, max_hp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    character["id"],
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
                    character["hp"]["current"],
                    character["hp"]["max"],
                ))

        self.db.commit()
        return character["id"]

