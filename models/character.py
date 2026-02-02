from .base import Actor, ClassFeature
from .race import Race, ATTRIBUTE_KEYS
from .weapon import Weapon
from .dndclass import DnDClass
import random
from typing import Optional

class Character(Actor):
    MAX_LEVEL = 20
   
    def __init__(self, id: str, name: str, race: Race, dnd_class:DnDClass):
        self.attributes = race.attributes.copy()
        super().__init__(id, name, self.attributes)

        self.name = name
        self.level = 1
        self.dnd_class = dnd_class
        self.race = race
        self.points = 0
        self.special_triats = race.special_traits.copy()
    
        self.weapon_proficiencies = dnd_class.weapon_proficiencies.copy()

        self.max_hp = self.dnd_class.hit_die + self.con_mod
        self.hp = self.max_hp

        self.proficiency_bonus = 2
        
        self.features: list[ClassFeature] = []
        self.apply_level_features()
    
    def can_levelUp(self):
        return self.level < self.MAX_LEVEL
    
    def levelUp(self):
        if not self.can_levelUp():
            return False
        self.level += 1
        if self.level in (4, 8, 12, 16, 19):
            self.points += 2
        self.apply_level_features()
        return True
    
    def assign_point(self, attribute: str, value: int = 1):
        if self.points < value:
            return False  # no hay suficientes puntos
        if attribute not in ATTRIBUTE_KEYS:
            return False  # atributo inválido

        self.attributes[attribute] += value
        self.points -= value
        return True
    
    def attack(self, target: Actor, advantage=False, disadvantage=False):
        if self.weapon:
            # Tirada de ataque
            tirada_ataque_total, tirada_dado, modificador, is_critical, is_fumble = self.roll(self.weapon.attribute, advantage, disadvantage)
            bonus_tirada = 0
            
            if self.inspiration_dice:
                fuente, info = next(iter(self.inspiration_dice.items()))
                usar = input(f"{self.name}, ¿usar dado de Bardic Inspiration ({tirada_ataque_total})? (s/n)").lower() == "s"
                if usar:
                    bonus_tirada += random.randint(1, info['die'])
                    del self.inspiration_dice[fuente]
                    tirada_ataque_total += bonus_tirada
                    

            if tirada_ataque_total >= target.calc_ac() and not is_fumble :
                damage = self.damage_roll(self.weapon, is_critical)
                bonus = 0
                for feature in self.features:
                    if getattr(feature, "active", False):  # Solo si está activa
                        bonus = getattr(feature, "get_damage_bonus", lambda: 0)()
                        damage += bonus

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
                    "damage_type": self.weapon.damage_type
                }
            else:
                return {
                    "hit": False,
                    "tirada_ataque_total": tirada_ataque_total,
                    "tirada_dado": tirada_dado,
                    "modificador": modificador,
                    "damage": 0,
                    "critical": is_critical,
                    "fumble": False,
                    "weapon": self.weapon.name,
                    "damage_type": self.weapon.damage_type
                }
        else:
            return {}
    
    def roll_hit_die(self, hit_die: int, con_mod: int, use_average=False):
        """
        Realiza una tirada de dado de golpe para subir de nivel.
        
        hit_die: número de caras del dado de golpe (6, 8, 10, 12)
        con_mod: modificador de Constitución
        use_average: si True, usa el promedio del dado en vez de tirar
        """
        if use_average:
            base = (hit_die // 2) + 1  # promedio del dado
        else:
            base = random.randint(1, hit_die)
        
        total = base + con_mod
        return max(1, total)  # siempre al menos 1 HP ganado

    def can_act(self) -> bool:
        if self.attributes["energy"] >= 3:
            self.attributes["energy"] -= 3
            return True
        else: return False
    
    def apply_level_features(self):
        feature_classes = self.dnd_class.features_by_level().get(self.level, [])
        for feature_cls in feature_classes:
            feature = feature_cls()
            feature.apply(self)  # Cada feature maneja su propio estado

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,

            "race": {
                "name": self.race.name,
                "key":self.race.key,
                "description": self.race.description,
                "special_traits": self.race.special_traits,
                "racial_bonus_stats": self.race.racial_bonus_stats
            },

            "class": {
                "name": self.dnd_class.name,
                "hit_die": self.dnd_class.hit_die,
                "weapon_proficiencies": self.weapon_proficiencies
            },

            "attributes": self.attributes,
            "points": self.points,

            "hp": {
                "current": self.hp,
                "max": self.max_hp
            },

            "proficiency_bonus": self.proficiency_bonus,

            "features": [
                {
                    "name": f.name,
                    "description": f.description,
                    "level_required": f.level
                }
                for f in self.features
            ]
        }


def create_character_Class(id: str, nombre: str, raza: Race, dnd_class: DnDClass):
    return Character(id, nombre, raza, dnd_class)