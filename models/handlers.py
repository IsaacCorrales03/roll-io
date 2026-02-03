import random
from .events import Event, EventContext, RollResult, ActionContext, EventHandler, GameState

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
