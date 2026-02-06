from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from collections import defaultdict
from uuid import UUID
from .EventContext import EventContext
from copy import deepcopy
from .Event import Event

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .EventDispatcher import EventDispatcher
    from .EventHandler import EventHandler
    from ..character import Character
    from ..querys import QueryHandler, Query

@dataclass
class GameState:
    characters: Dict[UUID, "Character"] = field(default_factory=dict)
    # NUEVO: recursos por actor
    resources: dict[UUID, dict[str, int]] = field(default_factory=dict)
    # Flujo global
    current_turn: int = 0
    current_actor: Optional[UUID] = None
    current_phase: Optional[str] = None  # combat | exploration | rest | dialogue
    current_day: int = 0
    # Orden de iniciativa (solo relevante en combate)
    initiative_order: List[UUID] = field(default_factory=list)
    dispatcher: "EventDispatcher" = field(default_factory=lambda: EventDispatcher())
    # Event sourcing light
    event_log: List["Event"] = field(default_factory=list)
    _handlers: dict = field(default_factory=dict)
    _query_handlers: dict = field(default_factory=dict)  # <QueryType, Handler>
    def register_handler(self, event_type: str, handler: EventHandler):
        self._handlers.setdefault(event_type, []).append(handler)
    def register_query_handler(self, query_type: type, handler: QueryHandler):
        self._query_handlers[query_type] = handler

    def query(self, query: Query) -> Any:
        """Router genérico para queries"""
        handler = self._query_handlers.get(type(query))
        if handler is None:
            raise RuntimeError(f"No hay handler registrado para query {type(query).__name__}")
        return handler.handle(query, self)


    def dispatch(self, event: Event):
        """Usar dispatcher para ejecutar handlers globales y features de actores"""
        self.event_log.append(event)
        self.dispatcher.dispatch(event, self)

    def run_readonly_event(self, root_event: Event) -> List[Event]:
        """
        Ejecuta un evento como simulación:
        - No altera el estado original del GameState
        - Permite que handlers y features modifiquen resultados temporalmente
        """
        shadow_state = deepcopy(self)
        collected: List[Event] = []

        # Wrapper temporal para registrar eventos en la lista local
        original_log = shadow_state.event_log
        shadow_state.event_log = collected  # en vez de mutar event_log real

        # Usar el dispatcher original
        self.dispatcher.dispatch(root_event, shadow_state)

        return collected

    def end_turn(self):
        expired_states = []

        for char in self.characters.values():
            if not hasattr(char, "status"):
                continue

            to_remove = []

            for status, data in char.status.items():
                # Validación dura
                if not isinstance(data, dict) or "turns" not in data:
                    raise RuntimeError(
                        f"Estado inválido '{status}' en actor {char.id}: {data}"
                    )

                data["turns"] -= 1

                if data["turns"] <= 0:
                    to_remove.append(status)

            for status in to_remove:
                del char.status[status]
                expired_states.append((char.id, status))

                self.dispatch(Event(
                    type="status_expired",
                    context=EventContext(actor_id=char.id),
                    payload={"status": status},
                    cancelable=False
                ))

        self.dispatch(Event(
            type="end_turn",
            payload={"turn": self.current_turn},
            cancelable=False
        ))

        self.current_turn += 1
        return expired_states

