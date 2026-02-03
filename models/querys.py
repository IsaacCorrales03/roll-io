from dataclasses import dataclass
from uuid import UUID
from typing import Any, List, TypeVar, Generic
from .events import GameState, Event, EventContext
from .results import *

# =======================
# Query base
# =======================

class Query:
    """Marker base. No lógica aquí."""
    pass

Q = TypeVar("Q", bound="Query")
R = TypeVar("R", bound="QueryResult")

class QueryHandler(Generic[Q, R]):
    def handle(self, query: Q, state: GameState) -> R:
        raise NotImplementedError


@dataclass(frozen=True)
class GetArmorClass(Query):
    actor_id: UUID
    context: str | None = None  # opcional: "attack", "ui", etc.

class GetArmorClassHandler(QueryHandler[GetArmorClass, ArmorClassResult]):
    def handle(self, query: GetArmorClass, state: GameState) -> ArmorClassResult:
        actor = state.characters.get(query.actor_id)
        if actor is None:
            raise RuntimeError("Actor no encontrado")

        # Evento de consulta (opcional, solo si otros sistemas reaccionan)
        event = Event(
            type="ac_requested",
            context=EventContext(
                actor_id=query.actor_id,
                phase=query.context
            ),
            payload={},
            cancelable=False
        )

        collected_events = state.run_readonly_event(event)

        # AC base REAL
        base_ac = None
        modifiers = []

        for ev in collected_events:
            if ev.type == "ac_base_calculated":
                base_ac = ev.payload["value"]       # reemplaza el base
            elif ev.type == "ac_modified":
                modifiers.append(ev.payload)        # sumas extras

        # Si ninguna feature reemplaza base → base default
        if base_ac is None:
            base_ac = actor.calc_ac()

        final_ac = base_ac + sum(m["value"] for m in modifiers)


        return ArmorClassResult(
            value=final_ac,
            breakdown=[
                {"source": "base", "value": base_ac},
                *modifiers
            ]
        )
