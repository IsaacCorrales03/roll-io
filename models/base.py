# El archivo base.py contiene las plantillas / clases abstractas para el funcionamiento general
# del sistema

from abc import ABC, abstractmethod
from typing import Optional
import random
from .weapon import Weapon
from uuid import UUID



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
    def cha_mod(self) -> int:
        return (self.attributes["CHA"] - 10) // 2
    
    @property
    def str_mod(self) -> int:
        return (self.attributes["STR"] - 10) // 2

    @property
    def int_mod(self) -> int:
        return (self.attributes["INT"] - 10) // 2
    @property
    def wis_mod(self) -> int:
        return (self.attributes["WIS"] - 10) // 2
        

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

    def calculate_base_ac(self):
        self.base_ac = self.calc_ac()

    def get_feature(self, name: str):
        for feature in self.features:
            if feature.name == name:
                return feature
        return None
