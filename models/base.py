# El archivo base.py contiene las plantillas / clases abstractas para el funcionamiento general
# del sistema

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Any, Dict
import random
from .weapon import Weapon
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from collections import defaultdict


class BaseEntity(ABC):
    def __init__(self, id:str, name: str):
        self.id = id
        self.name = name


class Action(BaseEntity, ABC):
    energy_cost: int = 3
    mana_cost: int = 0
    life_cost: int = 0

    @abstractmethod
    def requirements(self, actor: "Actor", context) -> bool:
        pass

    @abstractmethod
    def resolve(self, actor: "Actor", target: "Actor", context) -> dict:
        pass

class GameEvent(BaseEntity, ABC):
    @abstractmethod
    def trigger(self, context) -> bool:
        pass

    @abstractmethod
    def apply(self, context):
        pass





class Actor(ABC):
    """
    Actor es la clase abstracta para todas las entidades que interactuan y se relacionan con el entorno
    y otros actores
    """
    @property
    def con_mod(self) -> int:
        return (self.attributes["CON"] - 10) // 2

    @property
    def dex_mod(self) -> int:
        return (self.attributes["DEX"] - 10) // 2

    @property
    def cha_mod(self)-> int:
        return (self.attributes["CHA"] - 10) // 2
    
    @property
    def has_bardic_inspiration(self) -> bool:
        return self.bardic_inspiration_die != 0


    def consume_bardic_inspiration(self) -> int:
        if self.bardic_inspiration_die == 0:
            raise RuntimeError("No bardic inspiration available")

        die = self.bardic_inspiration_die
        self.bardic_inspiration_die = 0
        return random.randint(1, die)
    
    def __init__(self, id: UUID, name: str, attributes: dict):
        self.id = id
        self.name = name
        self.attributes = attributes
        self.active_effects = []
        self.features = []
        self.armor = None
        self.shield = None
        self.weapon: Optional[Weapon]
        self.hp = 0
        self.level = 0
        self.max_hp = 0
        self.base_ac: Optional[int] = None
        self.bardic_inspiration_die = 0
        self.inspiration_dice = {}  # key: ClassFeature instance, value: dict con 'die' y 'turns_left'


    @abstractmethod
    def can_act(self) -> bool:
        pass

    @abstractmethod
    def attack(self, target, advantage=False, disadvantage=False) -> dict:
        pass

    def calc_ac(self) -> int:
        """ Esta función se encarga de calcular y devolver el AC de un actor"""
        ac = 10 + self.dex_mod
        # Escudo
        if self.shield:
            ac += self.shield.bonus

        # Efectos activos
        for effect in self.active_effects:
            ac += effect.ac_bonus(self)

        return ac

    def equip(self, armor=None, weapon=None):
        """
        Función para equipar un arma u armadura en un actor
        """
        if armor:
            self.armor = armor
        if weapon:
            self.weapon = weapon

    def roll(self, attribute: str = "", advantage=False, disadvantage=False):
        """
        Realiza una tirada de dado d20 y devuelve el resultado con modificador, el resultado con dado, el modificador, 
        si fue crítico y si falló 
        """
        # Tirada de d20
        result = None
        is_critical = False
        is_fumble = False
        # Tirada de d20
        if advantage:
            rolls = [random.randint(1, 20) for _ in range(2)]
            result = max(rolls)
        elif disadvantage:
            rolls = [random.randint(1, 20) for _ in range(2)]
            result = min(rolls)
        else:
            result = random.randint(1, 20)
        is_critical = result == 20
        is_fumble = result == 1
        modifier = 0
        if attribute and attribute in self.attributes:
            modifier = (self.attributes[attribute] - 10) // 2
        total = result + modifier
        return total, result, modifier, is_critical, is_fumble
    
    def damage_roll(self, weapon, critical=False) -> int:
        """Realiza una tirada de daño, que recibe un arma, su dado y el daño que hace, devuelve el daño a reali"""
        total_dice = weapon.dice_count * 2 if critical else weapon.dice_count
        damage = sum(random.randint(1, weapon.dice_size) for _ in range(total_dice))
        modifier = (self.attributes[weapon.attribute] - 10) // 2 + weapon.bonus
        return damage + modifier

    def calculate_base_ac(self):
        self.base_ac = self.calc_ac()

    def get_feature(self, name: str):
        for feature in self.features:
            if feature.name == name:
                return feature
        return None
