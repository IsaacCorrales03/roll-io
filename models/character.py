from .base import Actor, ClassFeature
from .race import Race, ATTRIBUTE_KEYS
from .weapon import Weapon
from .dndclass import DnDClass
import random
from typing import Optional


class Character(Actor):
    MAX_LEVEL = 20  # Nivel máximo permitido

    def __init__(self, id: str, name: str, race: Race, dnd_class: DnDClass):
        # Atributos base heredados de la raza
        self.attributes = race.attributes.copy()
        super().__init__(id, name, self.attributes)

        # Identidad básica
        self.name = name
        self.level = 1

        # Referencias a raza y clase
        self.dnd_class = dnd_class
        self.race = race

        # Puntos para mejoras de atributos
        self.points = 0

        # Rasgos especiales raciales
        self.special_triats = race.special_traits.copy()

        # Competencias con armas según la clase
        self.weapon_proficiencies = dnd_class.weapon_proficiencies.copy()

        # Puntos de vida iniciales
        self.max_hp = self.dnd_class.hit_die + self.con_mod
        self.hp = self.max_hp

        # Bono de competencia inicial
        self.proficiency_bonus = 2

        # Lista de habilidades de clase activas
        self.features: list[ClassFeature] = []
        self.apply_level_features()

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
        if self.level in (4, 8, 12, 16, 19):
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
        return True

    def attack(self, target: Actor, advantage=False, disadvantage=False):
        # Ataque básico con arma equipada
        if not self.weapon:
            return {}

        # Tirada de ataque
        tirada_ataque_total, tirada_dado, modificador, is_critical, is_fumble = (
            self.roll(self.weapon.attribute, advantage, disadvantage)
        )

        bonus_tirada = 0

        # Uso opcional de inspiración
        if self.inspiration_dice:
            fuente, info = next(iter(self.inspiration_dice.items()))
            usar = input(
                f"{self.name}, ¿usar dado de Bardic Inspiration ({tirada_ataque_total})? (s/n)"
            ).lower() == "s"
            if usar:
                bonus_tirada += random.randint(1, info["die"])
                del self.inspiration_dice[fuente]
                tirada_ataque_total += bonus_tirada

        # Comprobación de impacto
        if tirada_ataque_total >= target.calc_ac() and not is_fumble:
            damage = self.damage_roll(self.weapon, is_critical)

            # Bonificadores de habilidades activas
            for feature in self.features:
                if getattr(feature, "active", False):
                    damage += getattr(feature, "get_damage_bonus", lambda: 0)()

            target.hp -= damage

            return {
                "hit": True,
                "tirada_ataque_total": tirada_ataque_total,
                "tirada_dado": tirada_dado,
                "modificador": modificador,
                "damage": damage,
                "bonus_tirada": bonus_tirada,
                "critical": is_critical,
                "fumble": False,
                "weapon": self.weapon.name,
                "damage_type": self.weapon.damage_type,
            }

        # Fallo del ataque
        return {
            "hit": False,
            "tirada_ataque_total": tirada_ataque_total,
            "tirada_dado": tirada_dado,
            "modificador": modificador,
            "damage": 0,
            "critical": is_critical,
            "fumble": False,
            "weapon": self.weapon.name,
            "damage_type": self.weapon.damage_type,
        }

    def roll_hit_die(self, hit_die: int, con_mod: int, use_average=False):
        # Tirada de dado de golpe al subir de nivel
        if use_average:
            base = (hit_die // 2) + 1
        else:
            base = random.randint(1, hit_die)

        return max(1, base + con_mod)

    def can_act(self) -> bool:
        # Control simple de energía por acción
        if self.attributes["energy"] >= 3:
            self.attributes["energy"] -= 3
            return True
        return False

    def apply_level_features(self):
        # Aplica las habilidades correspondientes al nivel actual
        feature_classes = self.dnd_class.features_by_level().get(self.level, [])
        for feature_cls in feature_classes:
            feature = feature_cls()
            feature.apply(self)

    def to_json(self) -> dict:
        # Serialización del personaje para API / frontend
        return {
            "id": self.id,
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
            "proficiency_bonus": self.proficiency_bonus,
            "features": [
                {
                    "name": f.name,
                    "description": f.description,
                    "level_required": f.level,
                }
                for f in self.features
            ],
        }


def create_character_Class(id: str, nombre: str, raza: Race, dnd_class: DnDClass):
    # Factory simple para creación de personajes
    return Character(id, nombre, raza, dnd_class)
