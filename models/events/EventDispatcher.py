from typing import Dict
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Event import Event
    from .EventHandler import EventHandler
    from .GameState import GameState



class EventDispatcher:
    def __init__(self):
        self._handlers: Dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: "EventHandler"):
        """Registrar handlers globales por tipo de evento"""
        self._handlers.setdefault(event_type, []).append(handler)

    def dispatch(self, event: "Event", state: "GameState"):
        """Despacha un evento a handlers globales y a features del actor"""
        # 1️⃣ Registrar el evento
        state.event_log.append(event)

        # 2️⃣ Ejecutar handlers globales
        for handler in self._handlers.get(event.type, []):
            handler.handle(event, state)

        # 3️⃣ Ejecutar features del actor objetivo
        actor_id = getattr(event.context, "actor_id", None)
        if actor_id is not None:
            actor = state.characters.get(actor_id)
            if actor:
                for feature in actor.features:
                    # Cada feature puede interceptar o ignorar
                    new_event = getattr(feature, "on_event", lambda e, s: None)(event, state)
                    if new_event:
                        # Re-emite el evento encadenado
                        self.dispatch(new_event, state)


