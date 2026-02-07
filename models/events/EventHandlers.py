from typing import TYPE_CHECKING
from uuid import UUID

from models.world.location import Location
from .EventHandler import EventHandler
from .Event import Event
from .EventContext import EventContext
from ..ProgresionSystem import ProgressionSystem
if TYPE_CHECKING:
    from .GameState import GameState


class LevelUpHandler:
    def handle(self, event, state):
        if event.type != "level_up":
            return
        actor = state.characters[event.context.actor_id]
        ProgressionSystem.apply(actor, state)

class ApplyDamageHandler(EventHandler):
    def handle(self, event: Event, state: GameState) -> None:
        if event.type != "attack_hit":
            return

        target_id = event.payload["target_id"]
        damage = event.payload["damage"]
        target = state.characters.get(target_id)
        if target:
            target.hp -= damage
            if target.hp <= 0:
                state.dispatch(Event(
                    type="entity_killed",
                    context=EventContext(actor_id=target.id),
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
            
class EnterLocationHandler(EventHandler):
    def handle(self, event: Event, state: GameState):
        if event.type != "enter_location":
            return

        ctx = event.context
        if ctx is None or ctx.actor_id is None or ctx.location_id is None:
            return

        actor = state.characters.get(ctx.actor_id)
        location_id = ctx.location_id

        if actor is None:
            return

        if location_id not in state.world_registry.locations:
            raise RuntimeError("Location inexistente")

        actor.current_location = location_id

        # Dispara efectos secundarios
        state.dispatch(Event(
            type="location_entered",
            context=ctx,
            payload={},
            cancelable=False
        ))

class RevealVisibilityHandler(EventHandler):
    def handle(self, event: Event, state: GameState):
        if event.type != "location_entered":
            return

        if event.context is None or event.context.location_id is None:
            return

        loc_id = event.context.location_id
        location = state.world_registry.get(Location, UUID(loc_id))

        for rule in location.visibility.revealed_by:
            if rule == "enter_city":
                break
        location.reveal()

class CreateLocationHandler(EventHandler):
    def handle(self, event: Event, state: GameState):
        if event.type != "create_location":
            return

        data = event.payload
        location = Location(**data)
        state.world_registry.add(location)
        state.dispatch(Event(
            type="location_created",
            context=event.context,
            payload={"location_id": str(location.id)},
            cancelable=False
        ))

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
