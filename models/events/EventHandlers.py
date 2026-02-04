from typing import TYPE_CHECKING
from .EventHandler import EventHandler

if TYPE_CHECKING:
    from .Event import Event
    from .GameState import GameState
    from .EventContext import EventContext

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
