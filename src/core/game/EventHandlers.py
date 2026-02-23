import random
from typing import TYPE_CHECKING
from uuid import UUID

from src.core.combat.phase import Phase
from src.core.character.enemy import Enemy
from src.features.world.domain.token import Token
from src.core.game.Event import Event, EventContext, EventHandler, GameState
from src.core.character.ProgresionSystem import ProgressionSystem



class LevelUpHandler(EventHandler):
    def handle(self, event, state):
        if event.type != "level_up":
            return
        actor = state.characters[event.context.actor_id] # type: ignore
        ProgressionSystem.apply(actor, state)

class ApplyDamageHandler(EventHandler):

    def handle(self, event: Event, state: GameState) -> None:

        if event.type != "attack_hit":
            return

        target_id = event.payload["target_id"]
        damage = event.payload["damage"]

        target = state.get_actor(target_id)
        if target is None:
            return

        target.hp -= damage

        if target.hp > 0:
            return

        # Clamp
        target.hp = 0

        # Remover de iniciativa
        if target.id in state.initiative_order:
            state.initiative_order.remove(target.id)

        # Emitir evento de muerte
        state.dispatch(Event(
            type="entity_killed",
            context=EventContext(actor_id=target.id),
            payload={},
            cancelable=False
        ))
        
        # Verificar fin de combate
        if state.current_phase == Phase.COMBAT:
            alive = [
                state.get_actor(a_id)
                for a_id in state.initiative_order
            ]

            # Separar equipos
            players_alive = any(a_id in state.characters for a_id in state.initiative_order)
            enemies_alive = any(a_id in state.enemies for a_id in state.initiative_order)

            if not players_alive or not enemies_alive:
                state.dispatch(Event(
                    type="combat_ended",
                    context=EventContext(),
                    payload={},
                    cancelable=False
                ))

class RageDamageHandler(EventHandler):
    def handle(self, event, state):
        if event.type != "attack_hit":
            return
        ctx = event.context
        if ctx is None or ctx.actor_id is None:
            return  # evento sin actor → no aplica rag
        actor = state.characters.get(ctx.actor_id)
        if actor is None:
            return
        rage = actor.status.get("rage")

        if not rage:
            return
        bonus = state.resources[actor.id]["rage_bonus"]

        event.payload["damage"] += bonus

        
class BardicInspirationHandler(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "roll_result":
            return

        if event.context is None:
            return

        actor_id = event.context.actor_id
        
        if actor_id is None:
            return
        
        actor = state.characters[actor_id]
        roll_value = event.payload["value"]


        if not actor.has_bardic_inspiration:
            return

        bonus = actor.consume_bardic_inspiration()

        modified_event = Event(
            type="roll_modified",
            source="system",
            context=event.context,
            payload={
                "original": roll_value,
                "bonus": bonus,
                "total": roll_value + bonus,
            }
        )

        state.event_log.append(modified_event)


class ApplyStatusHandler(EventHandler):
    def handle(self, event: Event, state: GameState):
        if event.type != "status_requested":
            return

        ctx = event.context
        if ctx is None or ctx.target_id is None:
            return

        target = state.characters.get(ctx.target_id)
        if target is None:
            return

        if not hasattr(target, "status"):
            target.status = {}

        target.status[event.payload["status"]] = {
            "turns":event.payload["duration_turns"]
        }

        state.dispatch(Event(
            type="status_applied",
            context=ctx,
            payload=event.payload,
            cancelable=False
        ))



class StunnedAttackHandler(EventHandler):
    def handle(self, event: Event, state: "GameState"):
        if event.type != "attack_roll":
            return  # Solo nos interesa ataques
        

        if not event.context:
            return
        attacker_id = event.context.actor_id
        target_id = event.context.target_id
        if not attacker_id or not target_id:
            return
        
        attacker = state.characters.get(attacker_id)
        if attacker:
            if hasattr(attacker, "status") and "aturdido" in attacker.status:
                roll_result = event.payload  # asumimos que contiene info del roll
                miss_event = Event(
                    type="attack_miss",
                    context=EventContext(actor_id=attacker_id, target_id=target_id),
                    payload={
                        "roll": roll_result.get("rolls"),
                        "attack_score": roll_result.get("attack_score"),
                        "stat_modifier": roll_result.get("stat_modifier"),
                        "target_ac": roll_result.get("target_ac"),
                        "reason": "aturdido",
                    },
                    cancelable=False
                )

                # Disparar el evento de ataque fallido
                state.dispatch(miss_event)

                # Cancelar el ataque original
                raise RuntimeError("Ataque cancelado por aturdimiento")
            

class EntityMovedHandler(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "entity_moved":
            return

        ctx = event.context
        if ctx is None or ctx.actor_id is None or ctx.location_id is None:
            return

        actor = state.characters.get(ctx.actor_id)
        if actor is None:
            return

        actor.current_location = ctx.location_id
        
class TokenMovedHandler(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "token_moved":
            return
        state.move_token(event.payload["token_id"], event.payload["x"], event.payload["y"])

class SpatialActionValidator(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "action_requested":
            return

        action = event.payload.get("action")
        if action != "attack":
            return

        ctx = event.context
        if ctx is None or ctx.actor_id is None or ctx.target_id is None:
            raise RuntimeError("Contexto incompleto")
        
        actor = state.characters.get(ctx.actor_id)
        target = state.characters.get(ctx.target_id)

        if actor is None or target is None:
            raise RuntimeError("Actor o target inexistente")

        if actor.current_location != target.current_location:
            raise RuntimeError("Objetivo fuera de alcance espacial")

class CreateEnemyHandler(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "create_enemy":
            return
        
        enemy = Enemy(
            id=event.payload["id"],
            name=event.payload["name"],
            hp=event.payload["hp"],
            size=event.payload["size"],
            max_hp=event.payload["max_hp"],
            ac=event.payload["ac"],
            asset_url=event.payload["asset_url"]
        )
        state.enemies[enemy.id] = enemy
        enemy_token = Token(
            id=enemy.id,  # Usamos el mismo UUID para el token
            actor_id=enemy.id,
            x=0,  # posición inicial por defecto
            y=0,
            size=enemy.size,
            texture_url=enemy.asset_url,
            label=enemy.name
        )
        state.add_token(enemy_token.to_dict())

        state.dispatch(Event(
            type="enemy_created",
            context=EventContext(actor_id=enemy.id),
            payload={
                "name": event.payload["name"],
                "hp": event.payload["hp"],
                "max_hp": event.payload["max_hp"],
                "ac": event.payload["ac"],
                "asset_url": event.payload["asset_url"]
            },
            cancelable=False
        ))

class InitiativeRollHandler(EventHandler):

    def handle(self, event: Event, state: GameState):

        if event.type != "initiative_roll_requested":
            return

        if not event.context or not event.context.actor_id:
            raise RuntimeError("initiative_roll_requested sin actor_id")

        actor_id = event.context.actor_id

        value = random.randint(1, 20)

        state.dispatch(Event(
            type="roll_result",
            context=EventContext(actor_id=actor_id),
            payload={
                "value": value,
                "reason": "initiative"
            },
            cancelable=False
        ))

class CombatStartedHandler(EventHandler):

    def handle(self, event, state):

        if event.type != "combat_started":
            return

        state.current_phase = Phase.COMBAT
        state.initiative_order = event.payload["initiative_order"]
        state.current_turn = 1
        state.current_actor = state.initiative_order[0]

        # Inicializar recursos
        for actor_id in state.initiative_order:
            actor = state.get_actor(actor_id)

            state.resources[actor_id] = {
                "action": 1,
                "bonus_action": 1,
                "movement": getattr(actor, "speed", 30),
                "reaction": 1
            }
            
class TurnStartHandler(EventHandler):

    def handle(self, event: Event, state: GameState):

        if event.type != "turn_started":
            return

        if not event.context or not event.context.actor_id:
            raise RuntimeError("turn_started sin actor_id")

        actor_id = event.context.actor_id

        combatant = state.get_combatant(actor_id)
        if not combatant:
            return

        combatant.reset_turn_resources()
        
class TurnEndedHandler(EventHandler):

    def handle(self, event, state):

        if event.type != "turn_ended":
            return

        current_index = state.initiative_order.index(state.current_actor) # type: ignore

        next_index = current_index + 1

        if next_index >= len(state.initiative_order):
            next_index = 0
            state.current_turn += 1

        state.current_actor = state.initiative_order[next_index]

        # Reset recursos del nuevo actor
        actor = state.get_actor(state.current_actor)

        state.resources[state.current_actor] = {
            "action": 1,
            "bonus_action": 1,
            "movement": getattr(actor, "speed", 30),
            "reaction": 1
        }

class CombatEndHandler(EventHandler):

    def handle(self, event, state):

        if event.type != "combat_ended":
            return

        for combatant in state.iter_combatants():
            combatant.clear_combat_effects()
        state.current_phase = Phase.EXPLORATION
        state.initiative_order.clear()
        state.current_actor = None

class CombatLogger(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type == "attack_roll":
            print(f"{state.get_actor(event.context.actor_id).name} attack_roll: {event.payload["attack_score"]}") # type: ignore

        elif event.type == "attack_hit":
            print(f"Hit! Damage: {event.payload['damage']}")

        elif event.type == "attack_miss":
            print("Miss!")

        elif event.type == "attack_failed":
            fallador = state.get_actor(event.context.actor_id) # type: ignore
            print(f"{fallador.name} falló el ataque por: {event.payload["reason"]}") #type: ignore
        elif event.type == "entity_killed":
            print(f"{state.get_actor(event.context.actor_id).name} died") # type: ignore

        elif event.type == "turn_ended":
            print("Turn ended")
        elif event.type == "combat_ended":
            print("Combate finalizado")
        