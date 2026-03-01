from abc import ABC, abstractmethod

from src.core.character.character import Character
from src.core.items.item import Weapon
from src.core.character.enemy import Enemy
from src.core.game.Event import EventContext, Event, GameState
from src.core.game.commands import *
from src.core.combat.phase import Phase
from src.core.game.querys import *
import random

class Action(ABC):
    @abstractmethod
    def execute(self, state: GameState) -> Event:
        pass


class RollAction:   
    def __init__(self, command: RollCommand) -> None:
        self.command = command

    def execute(self, state: "GameState") -> dict:
        actor = state.get_actor(self.command.actor_id)
        if actor is None:
            raise RuntimeError("Actor no encontrado")

        # Parsear dice string tipo "1d20+3"
        count, rest = self.command.dice.lower().split("d")
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
            if self.command.advantage:
                rolls.append(max(random.randint(1, size), random.randint(1, size)))
            elif self.command.disadvantage:
                rolls.append(min(random.randint(1, size), random.randint(1, size)))
            else:
                rolls.append(random.randint(1, size))

        total = sum(rolls) + bonus
        event = Event(
            type="roll_resolved",
            context=EventContext(actor_id=actor.id),
            payload={
                "dice": self.command.dice,
                "rolls": rolls,
                "bonus": bonus,
                "total": total,
                "reason": self.command.reason
            },
            cancelable=False
        )

        state.dispatch(event)
        return event.payload

class UseRageAction(Action):
    def __init__(self, actor_id):
        self.actor_id = actor_id

    def execute(self, state: GameState) -> Event:
        actor = state.characters.get(self.actor_id)
        if actor is None:
            return Event(
                type="rage_failed",
                context=EventContext(actor_id=self.actor_id),
                payload={"reason": "Actor no encontrado"},
                cancelable=False
            )

        # Declarar intención: entrar en rabia
        event = Event(
            type="rage_requested",
            context=EventContext(actor_id=actor.id),
            cancelable=True
        )

        state.dispatch(event)
        return event

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

    def execute(self, state: GameState) -> Event:

        # -----------------------
        # Validar fase
        # -----------------------
        if state.current_phase != Phase.COMBAT:
            failed_event = Event(
                type="attack_failed",
                context=EventContext(actor_id=self.command.actor_id),
                payload={"reason": "Not in combat phase"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        attacker = state.get_actor(self.command.actor_id)
        target = state.get_actor(self.command.target_id)

        if attacker is None or target is None:
            failed_event = Event(
                type="attack_failed",
                context=EventContext(actor_id=self.command.actor_id),
                payload={"reason": "Attacker or target not found"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        # -----------------------
        # Validar turno
        # -----------------------
        if state.current_actor != attacker.id:
            failed_event = Event(
                type="attack_failed",
                context=EventContext(actor_id=attacker.id),
                payload={"reason": "Not your turn"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        # -----------------------
        # Recursos
        # -----------------------
        actor_resources = state.resources.get(attacker.id, {})
        if actor_resources.get("action", 0) <= 0:
            failed_event = Event(
                type="attack_failed",
                context=EventContext(actor_id=attacker.id),
                payload={"reason": "No action available"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        # -----------------------
        # Seleccionar ataque
        # -----------------------
        if isinstance(attacker, Enemy):
            attack_name = getattr(self.command, "attack_name", None)
            if attack_name:
                weapon = attacker.get_attack(attack_name)
            else:
                weapon = attacker.choose_attack(target)
            stat_mod = 0
        else:
            weapon = getattr(attacker, "weapon", None)
            if weapon is None:
                failed_event = Event(
                    type="attack_failed",
                    context=EventContext(actor_id=attacker.id),
                    payload={"reason": "No weapon equipped"},
                    cancelable=False
                )
                state.dispatch(failed_event)
                return failed_event

            # Obtener modificador de atributo para héroe
            stat_mod_query = GetStatModifier(
                actor_id=attacker.id,
                attribute=weapon.attribute
            )
            stat_mod = state.query(stat_mod_query).value

        # -----------------------
        # Validar rango (opcional)
        # -----------------------
        if hasattr(attacker, "position") and hasattr(target, "position"):
            ax, ay = attacker.position
            tx, ty = target.position
            distance_tiles = abs(tx - ax) + abs(ty - ay)
            distance_feet = distance_tiles * 5

            weapon_range = getattr(weapon, "range", 5)
            if distance_feet > weapon_range:
                failed_event = Event(
                    type="attack_failed",
                    context=EventContext(actor_id=attacker.id),
                    payload={"reason": "Target out of range"},
                    cancelable=False
                )
                state.dispatch(failed_event)
                return failed_event

        # -----------------------
        # Tirada de ataque
        # -----------------------
        roll_command = RollCommand(
            actor_id=attacker.id,
            dice="1d20",
            reason="attack_throw",
            advantage=self.command.advantage,
            disadvantage=self.command.disadvantage
        )

        roll_result = RollAction(roll_command).execute(state)

        ac_query = GetArmorClass(actor_id=target.id, context="attack")
        target_ac = state.query(ac_query).value
        prof_bonus_query = GetProficiencyBonus(actor_id=attacker.id)
        prof_bonus = state.query(prof_bonus_query).value

        # Verificar si el personaje es competente con el arma
        is_proficient = False
        if hasattr(attacker, "dnd_class") and isinstance(attacker, Character) and isinstance(weapon, Weapon):
            is_proficient = weapon.proficiency_type in attacker.dnd_class.weapon_proficiencies

        proficiency_bonus = prof_bonus if is_proficient else 0
        print(proficiency_bonus)
        attack_bonus = (
            getattr(weapon, "bonus", 0) + stat_mod + proficiency_bonus
        )   
        attack_score = roll_result["total"] + attack_bonus

        natural_roll = roll_result["rolls"][0]
        critical = natural_roll == 20
        hit = critical or attack_score >= target_ac

        attack_roll_event = Event(
            type="attack_roll",
            context=EventContext(actor_id=attacker.id, target_id=target.id),
            payload={
                "natural_roll": natural_roll,
                "attack_score": attack_score,
                "target_ac": target_ac,
                "critical": critical,
                "hit": hit,
                "weapon": getattr(weapon, "name", "Enemy Attack")
            },
            cancelable=False
        )
        state.dispatch(attack_roll_event)

        if not hit:
            actor_resources["action"] -= 1
            miss_event = Event(
                type="attack_miss",
                context=EventContext(actor_id=attacker.id, target_id=target.id),
                payload={
                    "attack_score": attack_score,
                    "target_ac": target_ac
                },
                cancelable=False
            )
            state.dispatch(miss_event)
            return miss_event

        # -----------------------
        # Daño
        # -----------------------
        dice_expr = weapon.get_dice() if isinstance(attacker, Enemy) else weapon.dice_size

        damage_command = RollCommand(
            actor_id=attacker.id,
            dice=dice_expr, #type: ignore
            reason="damage"
        )

        damage_result = RollAction(damage_command).execute(state)
        damage_total = damage_result["total"] + stat_mod

        if critical:
            crit_command = RollCommand(
                actor_id=attacker.id,
                dice=dice_expr,#type: ignore
                reason="critical_damage"
            )
            crit_result = RollAction(crit_command).execute(state)
            damage_total += crit_result["total"]

        damage_event = Event(
            type="attack_hit",
            context=EventContext(actor_id=attacker.id, target_id=target.id),
            payload={
                "target_id": target.id,
                "damage": damage_total,
                "profiency": proficiency_bonus,
                "critical": critical,
                "weapon": getattr(weapon, "name", "Enemy Attack")
            },
            cancelable=False
        )
        state.dispatch(damage_event)

        actor_resources["action"] -= 1
        return damage_event
    
class StatusAction(Action):
    def __init__(self, command: StatusCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:
        event = Event(
            type="status_requested",
            context=EventContext(
                actor_id=self.command.actor_id,
                target_id=self.command.target_id
            ),
            payload={
                "status": self.command.status,
                "duration_turns": self.command.duration_turns
            },
            cancelable=True
        )
        state.dispatch(event)
        return event

class CreateEnemyAction(Action):
    def __init__(self, command: CreateEnemyCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:
        event = Event(
            type="create_enemy",
            context=EventContext(),
            payload={
                "name": self.command.name,
                "hp": self.command.hp,
                "max_hp": self.command.max_hp,
                "ac": self.command.ac,
                "asset_url": self.command.asset_url,
                "size": self.command.size
            },
            cancelable=True
        )
        state.dispatch(event)
        return event

class StartCombatAction(Action):

    def __init__(self, command: StartCombatCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:

        if state.current_phase == Phase.COMBAT:
            return Event(
                type="combat_failed",
                context=EventContext(),
                payload={"reason": "Combat already active"},
                cancelable=False
            )

        initiatives = []

        for actor_id in self.command.participant_ids:
            actor = state.get_actor(actor_id)
            if actor is None:
                continue

            # Tirada de iniciativa (1d20 + DEX mod)
            roll = random.randint(1, 20)

            dex_mod = state.query(
                GetStatModifier(actor_id=actor.id, attribute="DEX")
            ).value

            total = roll + dex_mod
            initiatives.append((actor.id, total))

        # Orden descendente
        initiatives.sort(key=lambda x: x[1], reverse=True)

        initiative_order = [actor_id for actor_id, _ in initiatives]

        event = Event(
            type="combat_started",
            context=EventContext(),
            payload={
                "initiative_order": initiative_order
            },
            cancelable=False
        )

        state.dispatch(event)
        return event
    
class EndTurnAction(Action):
    def __init__(self, command: EndTurnCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:

        actor = state.get_actor(self.command.actor_id)
        if actor is None:
            failed_event = Event(
                type="turn_end_failed",
                context=EventContext(actor_id=self.command.actor_id),
                payload={"reason": "Actor no encontrado"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        if state.current_actor != actor.id:
            failed_event = Event(
                type="turn_end_failed",
                context=EventContext(actor_id=actor.id),
                payload={"reason": "No es tu turno"},
                cancelable=False
            )
            state.dispatch(failed_event)
            return failed_event

        # Terminar turno: actualiza recursos y elimina estados expirados
        expired_states = state.end_turn()

        # Se puede disparar un evento global de fin de turno
        turn_ended_event = Event(
            type="turn_ended",
            context=EventContext(actor_id=actor.id),
            payload={
                "next_actor": state.current_actor,
                "expired_states": expired_states
            },
            cancelable=False
        )
        state.dispatch(turn_ended_event)

        return turn_ended_event