import random
from .events.Event import Event
from .events.EventContext import EventContext
from .events.GameState import GameState
from abc import ABC, abstractmethod
from .commands import *
from .querys import *
import random

class Action(ABC):
    @abstractmethod
    def execute(self, state: GameState) -> Event:
        pass

class RollAction:
    def execute(self, command: RollCommand, state: "GameState") -> dict:
        actor = state.characters.get(command.actor_id)
        if actor is None:
            raise RuntimeError("Actor no encontrado")

        # Parsear dice string tipo "1d20+3"
        count, rest = command.dice.lower().split("d")
        count = int(count)
        if "+" in rest:
            size, bonus = rest.split("+")
            size = int(size)
            bonus = int(bonus)
        else:
            size = int(rest)
            bonus = 0

        # Tiradas con ventaja/desventaja
        rolls = []
        for _ in range(count):
            if command.advantage:
                rolls.append(max(random.randint(1, size), random.randint(1, size)))
            elif command.disadvantage:
                rolls.append(min(random.randint(1, size), random.randint(1, size)))
            else:
                rolls.append(random.randint(1, size))

        total = sum(rolls) + bonus
        event = Event(
            type="roll_resolved",
            context=EventContext(actor_id=actor.id),
            payload={
                "dice": command.dice,
                "rolls": rolls,
                "bonus": bonus,
                "total": total,
                "reason": command.reason
            },
            cancelable=False
        )

        state.dispatch(event)
        return event.payload

class UseSongOfRestAction(Action):
    def __init__(self, command: UseSongOfRestCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:
        actor = state.characters[self.command.actor_id]
        # La feature activa contiene la lógica
        song = actor.get_feature("SongOfRest")  # búsqueda por nombre
        if song:
            return song.use(actor, state, targets=self.command.targets)
        else: 
            return Event(
                type="song_of_rest_failed",
                context=EventContext(actor_id=actor.id),
                payload={"reason": "Habilidad no aprendida"},
                cancelable=False
            )

class AttackAction(Action):
    def __init__(self, command: AttackCommand):
        self.command = command

    def execute(self, state: "GameState") -> Event:
        attacker = state.characters.get(self.command.actor_id)
        target = state.characters.get(self.command.target_id)

        if attacker is None or target is None:
            return Event(
                type="attack_failed",
                context=EventContext(actor_id=self.command.actor_id),
                payload={"reason": "Atacante o objetivo no encontrado"},
                cancelable=False
            )

        weapon = getattr(attacker, "weapon", None)
        if weapon is None:
            return Event(
                type="attack_failed",
                context=EventContext(actor_id=attacker.id),
                payload={"reason": "No tiene arma equipada"},
                cancelable=False
            )
        # Usar RollAction para la tirada de ataque
        roll_command = RollCommand(
            actor_id=attacker.id,
            dice="1d20",
            reason="attack_throw",
            advantage=self.command.adventage,
            disadvantage=self.command.disadventage
        )
        roll_result = RollAction().execute(roll_command, state)
        ac_query = GetArmorClass(actor_id=target.id, context="attack")
        target_ac = state.query(ac_query).value
        stat_mod_query = GetStatModifier(actor_id=attacker.id,attribute = weapon.attribute )
        stat_mod = state.query(stat_mod_query).value
        attack_score = roll_result["total"] + stat_mod
        hit = attack_score >= target_ac 

        # Evento de tirada de ataque
        attack_roll_event = Event(
            type="attack_roll",
            context=EventContext(actor_id=attacker.id),
            payload={
                "roll": roll_result["rolls"],
                "bonus": attacker.weapon.bonus if attacker.weapon else 0 ,
                "attack_score": attack_score,
                "target_ac": target.calc_ac(),
                "hit": hit,
                "attacker_id": attacker.id,
                "target_id": target.id,
                "weapon": weapon.name
            },
            cancelable=False
        )
        state.dispatch(attack_roll_event)
        
        if hit:
            damage_command = RollCommand(
                actor_id=attacker.id,
                dice=attacker.weapon.dice_size if attacker.weapon else "1d6",
                reason="damage"
            )
            damage = RollAction().execute(damage_command, state)
            damage_event = Event(
                type="attack_hit",
                context=EventContext(actor_id=attacker.id),
                payload={
                    "damage": damage["total"],
                    "target_id": target.id,
                    "weapon": weapon.name,
                    "stat_modifier": stat_mod
                },
                cancelable=False
            )
            state.dispatch(damage_event)
            return damage_event
        else:
            miss_event = Event(
                type="attack_miss",
                context=EventContext(actor_id=attacker.id, target_id=target.id),
                payload={
                    "roll": roll_result["rolls"],
                    "attack_score": attack_score,
                    "stat_modifier": stat_mod,
                    "target_ac": target_ac,
                    "stat_modifier": stat_mod
                },
                cancelable=False
            )
            state.dispatch(miss_event)
            return miss_event
