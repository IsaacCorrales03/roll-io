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
                        hp, max_hp, texture
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
                print(character)
                # Saving throws
                for ability in character.get("saving_throw_proficiencies", []):
                    cursor.execute("""
                        INSERT INTO character_saving_throw_proficiencies
                        (character_id, ability_key)
                        VALUES (%s, %s)
                    """, (str(character["id"]), ability))


                # Weapon proficiencies
                for weapon in character.get("weapon_proficiencies", []):
                    cursor.execute("""
                        INSERT INTO character_weapon_proficiencies
                        (character_id, weapon_key)
                        VALUES (%s, %s)
                    """, (str(character["id"]), weapon))


                # Armor proficiencies
                for armor in character.get("armor_proficiencies", []):
                    cursor.execute("""
                        INSERT INTO character_armor_proficiencies
                        (character_id, armor_key)
                        VALUES (%s, %s)
                    """, (str(character["id"]), armor))

                for skill in character.get("skill_proficiencies", []):
                    cursor.execute("""
                        INSERT INTO character_skill_proficiencies
                        (character_id, skill_key)
                        VALUES (%s, %s)
                    """, (str(character["id"]), skill))
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
                (str(character["id"]),)
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
                        texture = %s

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
                    str(character["id"]),
                    character["texture"]
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


    def save_inventory(self, character_id: str, inventory: dict[str, dict]):
        with self.db.cursor() as cursor:

            cursor.execute(
                "DELETE FROM character_inventory WHERE character_id = %s",
                (character_id,)
            )

            for item_id, data in inventory.items():
                cursor.execute("""
                    INSERT INTO character_inventory
                    (id, character_id, item_id, quantity, equipped)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()),       # <--- id obligatorio
                    character_id,
                    item_id,
                    data["quantity"],
                    data.get("equipped", False)
                ))


        self.db.commit()


    def get_inventory(self, character_id: str):
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT item_id, quantity, equipped FROM character_inventory WHERE character_id = %s",
                (character_id,)
            )
            return cursor.fetchall()

    def get_proficiencies(self, character_id: str) -> dict:
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT ability_key FROM character_saving_throw_proficiencies WHERE character_id = %s",
                (character_id,)
            )
            saving_throws = [row["ability_key"] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT weapon_key FROM character_weapon_proficiencies WHERE character_id = %s",
                (character_id,)
            )
            weapons = [row["weapon_key"] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT armor_key FROM character_armor_proficiencies WHERE character_id = %s",
                (character_id,)
            )
            armors = [row["armor_key"] for row in cursor.fetchall()]

        return {
            "saving_throw_proficiencies": saving_throws,
            "weapon_proficiencies": weapons,
            "armor_proficiencies": armors,
        }