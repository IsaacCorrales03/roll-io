from uuid import uuid4
from src.core.base import Movement
from dataclasses import dataclass

@dataclass
class EnemyAttack:
    name: str
    dice_count: int
    dice_size: int
    damage_bonus: int
    attack_bonus: int
    damage_type: str = "slashing"

    def get_dice(self) -> str:
        """
        Devuelve la expresión de dado lista para RollAction, ejemplo "1d6+2".
        """
        bonus_str = f"+{self.damage_bonus}" if self.damage_bonus else ""
        return f"{self.dice_count}d{self.dice_size}{bonus_str}"
    

class Enemy:
    def __init__(self, id, name, hp, max_hp, ac, asset_url, size=(1, 1), attributes: dict[str, int] | None = None, attacks: list[EnemyAttack] | None = None):
        self.id = id
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.ac = ac
        self.size = size
        self.asset_url = asset_url
        self.movement = Movement(base_speed=30)
        self.action_available = True
        self.reaction_available = True
        self.active_conditions = []
        self.temp_bonuses = []
        self.position = (0,0)
        self.attributes = attributes or {
            "STR": 10,
            "DEX": 10,
            "CON": 10,
            "INT": 10,
            "WIS": 10,
            "CHA": 10,
        }
        self.attacks = attacks or []
    def to_dict(self):  
        return {
            "id": str(self.id),
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "ac": self.ac,
            "asset_url": self.asset_url
        }

    def reset_turn_resources(self) -> None:
        self.action_available = True
        self.reaction_available = True
        self.movement.reset()
    def clear_combat_effects(self) -> None:
        self.active_conditions.clear()
        self.temp_bonuses.clear()

    def calc_ac(self):
        return self.ac
    
    def get_attack(self, attack_name: str) -> EnemyAttack:
        for atk in self.attacks:
            if atk.name == attack_name:
                return atk
        raise ValueError(f"Attack {attack_name} not found")
    
    def choose_attack(self, target) -> EnemyAttack:
        return self.attacks[0]