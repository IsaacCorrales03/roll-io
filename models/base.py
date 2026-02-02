from abc import ABC, abstractmethod
from typing import List, Callable, Optional
import random
from .weapon import Weapon

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

class ClassFeature(ABC):
    name: str
    description: str
    level: int

    @classmethod
    def info(cls) -> dict:
        return {
            "name": cls.name,
            "description": cls.description,
            "level": cls.level
        }
    
    def __init__(self):
        pass
    @abstractmethod
    def apply(self, actor: "Actor"):
        pass

    @abstractmethod
    def use(self, actor: "Actor", turn_manager) -> dict:
        """Usa la feature si es activable."""
        pass

class Actor(ABC):
    @property
    def con_mod(self) -> int:
        return (self.attributes["CON"] - 10) // 2

    @property
    def dex_mod(self) -> int:
        return (self.attributes["DEX"] - 10) // 2

    @property
    def cha_mod(self)-> int:
        return (self.attributes["CHA"] - 10) // 2
 
    def __init__(self, id: str, name: str, attributes: dict):
        self.id = id
        self.name = name
        self.attributes = attributes
        self.features: List[ClassFeature] = []
        self.ac_formulas: List[Callable[["Actor"], int]] = []
        self.active_effects = []
        self.armor = None
        self.shield = None
        self.weapon: Optional[Weapon]
        self.hp = 0
        self.level = 0
        self.max_hp = 0
        self.inspiration_dice = {}  # key: ClassFeature instance, value: dict con 'die' y 'turns_left'


    @abstractmethod
    def can_act(self) -> bool:
        pass

    @abstractmethod
    def attack(self, target, advantage=False, disadvantage=False) -> dict:
        pass

    def calc_ac(self) -> int:
    
        ac_candidates = []

        # Base AC
        if self.armor:
            ac_candidates.append(self.armor.ac(self))
        else:
            ac_candidates.append(10 + self.dex_mod)

        # Fórmulas de features
        for formula in self.ac_formulas:
            val = formula(self)
            if val > 0:
                ac_candidates.append(val)

        ac = max(ac_candidates)

        # Escudo
        if self.shield:
            ac += self.shield.bonus

        # Efectos activos
        for effect in self.active_effects:
            ac += effect.ac_bonus(self)

        return ac

    def equip(self, armor=None, weapon=None):
        if armor:
            self.armor = armor
        if weapon:
            self.weapon = weapon

    def roll(self, attribute: str = "", advantage=False, disadvantage=False):
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
            total_dice = weapon.dice_count * 2 if critical else weapon.dice_count
            damage = sum(random.randint(1, weapon.dice_size) for _ in range(total_dice))
            modifier = (self.attributes[weapon.attribute] - 10) // 2 + weapon.bonus
            return damage + modifier


    def apply_bardic_inspiration(self, total: int, attribute: str = "") -> int:
        """
        Si el actor tiene un dado de inspiración activo, permite usarlo.
        Se llama **después de tirar el d20**.
        """
        if not self.inspiration_dice:
            return total  # no hay dado activo

        # Tomamos el primer dado disponible
        source, info = next(iter(self.inspiration_dice.items()))
        bonus = random.randint(1, info["die"])
        del self.inspiration_dice[source]  # el dado se consume al usarlo
        print(f"{self.name} usa un dado de inspiración: +{bonus}")
        return total + bonus
