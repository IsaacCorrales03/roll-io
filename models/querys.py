from dataclasses import dataclass
from uuid import UUID
from typing import Any, List, TypeVar, Generic
from math import floor
from models.results import StatModifierResult
from .events.Event import Event
from .events.EventContext import EventContext
from .events.GameState import GameState
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

@dataclass(frozen=True)
class GetStatModifier(Query):
    actor_id: UUID
    attribute: str

class GetStatModifierHandler(QueryHandler[GetStatModifier, StatModifierResult]):
    def handle(self, query: GetStatModifier, state: GameState) -> StatModifierResult:
        actor = state.characters.get(query.actor_id)
        if actor is None:
            raise RuntimeError("Actor no encontrado")

        # Evento opcional para que otras features modifiquen temporalmente el modifier
        event = Event(
            type="stat_modifier_requested",
            context=EventContext(actor_id=query.actor_id),
            payload={"attribute": query.attribute},
            cancelable=False
        )
        collected_events = state.run_readonly_event(event)

        # Modifier base (según regla de D&D)
        base_value = floor((actor.attributes[query.attribute] - 10) / 2)
        modifiers = []

        # Procesar cualquier modificación adicional desde eventos
        for ev in collected_events:
            if ev.type == "stat_modifier_modified":
                modifiers.append(ev.payload)  # ejemplo: {"source": "buff", "value": 1}

        final_value = base_value + sum(m["value"] for m in modifiers)

        return StatModifierResult(
            value=final_value,
            breakdown=[{"source": "base", "value": base_value}, *modifiers]
        )