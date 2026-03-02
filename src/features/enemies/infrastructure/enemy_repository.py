import uuid
from typing import Optional, Dict, Any, List, cast
from src.shared.database.db_service import create_db_service


class EnemyRepository:
    def __init__(self):
        self.db = create_db_service()

    # =========================
    # CREATE
    # =========================
    def create(self, enemy: Dict[str, Any], owner_id: uuid.UUID) -> str:
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO enemies (
                    id, owner_id, name,
                    hp, max_hp, ac,
                    asset_url,
                    size_x, size_y,
                    str, dex, con,
                    int_stat, wis, cha
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(enemy["id"]),
                str(owner_id),
                enemy["name"],
                enemy["hp"],
                enemy["max_hp"],
                enemy["ac"],
                enemy.get("asset_url"),
                enemy.get("size", (1, 1))[0],
                enemy.get("size", (1, 1))[1],
                enemy["attributes"]["STR"],
                enemy["attributes"]["DEX"],
                enemy["attributes"]["CON"],
                enemy["attributes"]["INT"],
                enemy["attributes"]["WIS"],
                enemy["attributes"]["CHA"],
            ))

            # Attacks
            for attack in enemy.get("attacks", []):
                cursor.execute("""
                    INSERT INTO enemy_attacks (
                        id, enemy_id, name,
                        dice_count, dice_size,
                        damage_bonus, attack_bonus,
                        damage_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()),
                    str(enemy["id"]),
                    attack["name"],
                    attack["dice_count"],
                    attack["dice_size"],
                    attack.get("damage_bonus", 0),
                    attack.get("attack_bonus", 0),
                    attack.get("damage_type", "slashing"),
                ))

        self.db.commit()
        return enemy["id"]

    # =========================
    # GET
    # =========================
    def get_by_id(self, enemy_id: str) -> Optional[Dict[str, Any]]:
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM enemies WHERE id = %s",
                (enemy_id,)
            )
            enemy = cursor.fetchone()

            if not enemy:
                return None

            cursor.execute(
                "SELECT * FROM enemy_attacks WHERE enemy_id = %s",
                (enemy_id,)
            )
            attacks = cursor.fetchall()

        enemy["attacks"] = attacks
        return cast(Optional[Dict[str, Any]], enemy)

    def get_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        with self.db.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM enemies WHERE owner_id = %s",
                (owner_id,)
            )
            return cast(List[Dict[str, Any]], cursor.fetchall())

    # =========================
    # DELETE
    # =========================
    def delete(self, enemy_id: str) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM enemies WHERE id = %s",
                (enemy_id,)
            )
            deleted = cursor.rowcount > 0

        self.db.commit()
        return deleted

    # =========================
    # UPDATE / SAVE
    # =========================
    def save(self, enemy: Dict[str, Any], owner_id: uuid.UUID) -> str:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM enemies WHERE id = %s",
                (str(enemy["id"]),)
            )
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE enemies SET
                        name = %s,
                        hp = %s,
                        max_hp = %s,
                        ac = %s,
                        asset_url = %s,
                        size_x = %s,
                        size_y = %s,
                        str = %s,
                        dex = %s,
                        con = %s,
                        int_stat = %s,
                        wis = %s,
                        cha = %s,
                        owner_id = %s
                    WHERE id = %s
                """, (
                    enemy["name"],
                    enemy["hp"],
                    enemy["max_hp"],
                    enemy["ac"],
                    enemy.get("asset_url"),
                    enemy.get("size", (1, 1))[0],
                    enemy.get("size", (1, 1))[1],
                    enemy["attributes"]["STR"],
                    enemy["attributes"]["DEX"],
                    enemy["attributes"]["CON"],
                    enemy["attributes"]["INT"],
                    enemy["attributes"]["WIS"],
                    enemy["attributes"]["CHA"],
                    str(owner_id),
                    str(enemy["id"]),
                ))
            else:
                return self.create(enemy, owner_id)

            # Reemplazar ataques (estrategia simple y segura)
            cursor.execute(
                "DELETE FROM enemy_attacks WHERE enemy_id = %s",
                (str(enemy["id"]),)
            )

            for attack in enemy.get("attacks", []):
                cursor.execute("""
                    INSERT INTO enemy_attacks (
                        id, enemy_id, name,
                        dice_count, dice_size,
                        damage_bonus, attack_bonus,
                        damage_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()),
                    str(enemy["id"]),
                    attack["name"],
                    attack["dice_count"],
                    attack["dice_size"],
                    attack.get("damage_bonus", 0),
                    attack.get("attack_bonus", 0),
                    attack.get("damage_type", "slashing"),
                ))

        self.db.commit()
        return enemy["id"]