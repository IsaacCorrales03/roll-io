from abc import ABC, abstractmethod
from .base import Actor
from .character import Character
import random

class Enemy(Actor, ABC):
    def __init__(self, id: str, name: str, attributes: dict[str,int], party: list[Character]):
        self.id = id
        self.name = name
        self.attributes = attributes
        self.actions = ["Attack"]
        self.party = party
        self.hp_actual = attributes["hp"]
        super().__init__(id, name, attributes)

    def can_act(self) -> bool:
        return super().can_act()
    
    @abstractmethod
    def define_objetive(self) -> Character:
        pass

    def attack(self, attack_type: str):
        objetivo = self.define_objetive()
        if attack_type == "magic":
            attack = self.attributes["magic_power"]
        elif attack_type == "physical":
            attack = self.attributes["strength"]
        elif attack_type == "true":
            attack = self.attributes["strength"] 
        else:
            raise ValueError(f"Tipo de ataque inválido: {attack_type}")

        defense = objetivo.get_defense(attack_type)
        damage = attack * (attack / (attack + defense))
        is_critical = self.can_critical()
        if is_critical:
            damage *= self.CRIT_BONUS
        
        damage = int(damage)
        objetivo.apply_damage(damage)
        return {
             "target": objetivo,
             "damage": damage,
             "critical": is_critical
        }

        
