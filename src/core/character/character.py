from typing import Optional

from src.core.items.item import ItemInstance, Weapon

from ..base import Actor
from .ClassFeature import ClassFeature
from .race import Race, ATTRIBUTE_KEYS
from .dndclass import DnDClass
import random
import uuid

class Character(Actor):
    """Representa un personaje de Dungeons & Dragons con raza, clase y atributos asociados.
    Gestiona el progreso de nivel, puntos de vida, rasgos de clase y acciones básicas de combate.
    """
    MAX_LEVEL = 20  # Nivel máximo permitido

    def __init__(self, id: uuid.UUID, owner_id : uuid.UUID, name: str, race: Race, dnd_class: DnDClass):
        # Atributos base heredados de la raza
        self.attributes = race.attributes.copy()
        super().__init__(id, name, self.attributes)
        self.owner_id = owner_id

        # Identidad básica
        self.name = name
        self.level = 1
        self.texture = None
        # Referencias a raza y clase
        self.dnd_class = dnd_class
        self.race = race

        # Puntos para mejoras de atributos
        self.points = 0

        # Rasgos especiales raciales
        self.special_traits = race.special_traits.copy()
        # Competencias con armas según la clase
        self.weapon_proficiencies = dnd_class.weapon_proficiencies.copy()
        # Puntos de vida iniciales
        self.max_hp = self.dnd_class.hit_die + self.con_mod
        self.hp = self.max_hp

        # Bono de competencia inicial
        self.proficiency_bonus = 2
        self.current_location = ""
        # Lista de habilidades de clase activas
        self.features: list[ClassFeature] = []
        self.status: dict = {}
        self.apply_level_features()
        self.inventory: list[ItemInstance] = []
        self.max_weight = self.attributes["STR"] * 15

    def can_levelUp(self):
        # Verifica si aún puede subir de nivel
        return self.level < self.MAX_LEVEL

    def levelUp(self, use_average=True):
        if not self.can_levelUp():
            return False

        self.level += 1

        # Aumento de vida por nivel
        hp_gained = self.roll_hit_die(
            self.dnd_class.hit_die,
            self.con_mod,
            use_average=use_average

        )
        self.max_hp += hp_gained
        self.hp += hp_gained  # curación automática al subir de nivel

        # ASI
        if self.level in {4, 8, 12, 16, 19}:
            self.points += 2

        self.apply_level_features()
        return True

    def assign_point(self, attribute: str, value: int = 1):
        # Asigna puntos a atributos válidos
        if self.points < value:
            return False
        if attribute not in ATTRIBUTE_KEYS:
            return False

        self.attributes[attribute] += value
        self.points -= value
        self.max_weight = self.attributes["STR"] * 15
        return True

    def roll_hit_die(self, hit_die: int, con_mod: int, use_average=False):
        # Tirada de dado de golpe al subir de nivel
        base = (hit_die // 2) + 1 if use_average else random.randint(1, hit_die)
        return max(1, base + con_mod)

    def apply_level_features(self):
        # 1) Obtener features por nivel
        feature_classes = self.dnd_class.features_by_level().get(self.level, [])

        for feature_cls in feature_classes:
            feature = feature_cls()
            feature.level = self.level  # asigna nivel del personaje
            # 2) Registrar la feature en el actor
            self.features.append(feature)

    def current_weight(self) -> float:
        return sum(
            item.item.weight * item.quantity
            for item in self.inventory
        )
    
    def can_carry(self, item_instance: "ItemInstance") -> bool:
        new_weight = item_instance.item.weight * item_instance.quantity
        return self.current_weight() + new_weight <= self.max_weight
    
    def add_item(self, item_instance: "ItemInstance") -> bool:
        if not self.can_carry(item_instance):
            return False

        if item_instance.item.stackable:
            for existing in self.inventory:
                if existing.item.item_id == item_instance.item.item_id:
                    existing.quantity += item_instance.quantity
                    return True

        self.inventory.append(item_instance)
        return True

    def load_inventory(self, items_data: list[dict]) -> None:
        from src.core.items.items import ITEMS

        self.inventory.clear()

        for entry in items_data:
            item = ITEMS.get(entry["item_id"])
            if not item:
                continue

            instance = ItemInstance(
                item=item,
                quantity=entry.get("quantity", 1),
            )

            instance.equipped = entry.get("equipped", False)

            self.add_item(instance)

            # Equipar si estaba marcado como equipado
            if instance.equipped:
                self.equip(instance)





    def to_json(self) -> dict:
        # Serialización del personaje para API / frontend
        return {
            "id": str(self.id),
            "name": self.name,
            "level": self.level,
            "race": {
                "name": self.race.name,
                "key": self.race.key,
                "description": self.race.description,
                "special_traits": self.race.special_traits,
                "racial_bonus_stats": self.race.racial_bonus_stats,
            },
            "class": {
                "name": self.dnd_class.name,
                "hit_die": self.dnd_class.hit_die,
                "weapon_proficiencies": self.weapon_proficiencies,
            },
            "attributes": self.attributes,
            "points": self.points,
            "hp": {
                "current": self.hp,
                "max": self.max_hp,
            },
            "weapon": {
                "name": self.weapon.name if self.weapon else None,
                "description": self.weapon.description if self.weapon else None,
                "damage_type": self.weapon.damage_type if self.weapon else None,
                "dice_count": self.weapon.dice_count if self.weapon else None,
                "dice_size": self.weapon.dice_size if self.weapon else None,
                "bonus": self.weapon.bonus if self.weapon else None,
                "attribute": self.weapon.attribute if self.weapon else None,
            },
            "armor": {
                "name": self.armor.name if self.armor else None,
                "description": self.armor.description if self.armor else None,
                "base_ac": self.armor.base_ac if self.armor else None,
                "dex_bonus": self.armor.dex_bonus if self.armor else None,  
                "dex_bonus_limit": self.armor.dex_bonus_limit if self.armor else None,
                "stealth_disadvantage": self.armor.stealth_disadvantage if self.armor else None,
            },
            "shield": {
                "name": self.shield.name if self.shield else None,
                "description": self.shield.description if self.shield else None,
                "ac_bonus": self.shield.ac_bonus if self.shield else None,
            },
            "proficiency_bonus": self.proficiency_bonus,
            "features": [
                {
                    "name": f.name,
                    "type": f.type,
                    "description": f.description,
                    "level_required": f.level,
                }
                for f in self.features
            ],
            "texture": self.texture,
            "inventory": [
                {
                    "item_id": str(instance.item.item_id),
                    "quantity": instance.quantity,
                    "equipped": instance.equipped,
                    "durability": instance.durability,
                    "meta": {
                        "name": instance.item.name,
                        "weight": instance.item.weight,
                        "description": instance.item.description,
                        "item_type": instance.item.item_type,
                    }
                }
                for instance in self.inventory
            ],
            "max_weight": self.max_weight,
            "current_weight": self.current_weight(),

        }
    
    @classmethod
    def from_dict(
        cls,
        data: dict,
        race: Race,
        dnd_class: DnDClass,
    ) -> "Character":
        """
        Reconstruye un Character desde datos persistidos (DB).
        Asume que race y dnd_class ya están resueltas por key.
        """

        char = cls(
            id=uuid.UUID(data["id"]),
            owner_id=uuid.UUID(data["owner_id"]),
            name=data["name"],
            race=race,
            dnd_class=dnd_class,
        )

        # ---- estado básico ----
        char.level = data["level"]
        char.attributes = {
            "STR": data["strength"],
            "DEX": data["dexterity"],
            "CON": data["constitution"],
            "INT": data["intelligence"],
            "WIS": data["wisdom"],
            "CHA": data["charisma"],
        }

        # ---- HP ----
        char.max_hp = data["max_hp"]
        char.hp = data["hp"]


        # ---- recalcular derivados ----
        char.proficiency_bonus = 2 + ((char.level - 1) // 4)
        char.texture = data.get("texture", None)
        # ---- features ----
        char.features.clear()
        for lvl in range(1, char.level + 1):
            feature_classes = dnd_class.features_by_level().get(lvl, [])
            for feature_cls in feature_classes:
                feature = feature_cls()
                feature.level = lvl
                feature.type = feature_cls.type
                char.features.append(feature)
        char.load_inventory(data.get("inventory", []))
        return char


def create_character_Class(id: uuid.UUID, owner_id: uuid.UUID, nombre: str, raza: Race, dnd_class: DnDClass):
    # Factory simple para creación de personajes
    return Character(id, owner_id, nombre, raza, dnd_class)