from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4, UUID
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from src.core.character.enemy import Enemy
from src.core.base import Actor
from src.core.game.query import Query, QueryHandler


@dataclass(frozen=True)
class Event:
    id: UUID = field(default_factory=uuid4)
    type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    context: Optional["EventContext"] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    cancelable: bool = False

@dataclass
class EventContext:
    actor_id: Optional[UUID] = None
    target_id: Optional[UUID] = None
    
    turn: Optional[int] = None
    phase: Optional[str] = None
    location_id: Optional[str] = None

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



class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: "Event", state: "GameState") -> None:
        pass


@dataclass
class GameState:
    
    characters: Dict[UUID, "Actor"] = field(default_factory=dict)
    tokens: Dict[UUID, dict] = field(default_factory=dict)
    enemies: Dict[UUID, "Enemy"] = field(default_factory=dict)
    # NUEVO: recursos por actor
    resources: dict[UUID, dict[str, int]] = field(default_factory=dict)
    # Flujo global
    current_turn: int = 0
    current_actor: Optional[UUID] = None
    current_phase: Optional[str] = None  # combat | exploration | rest | dialogue
    current_day: int = 0
    # Orden de iniciativa (solo relevante en combate)
    initiative_order: list[UUID] = field(default_factory=list)
    dispatcher: "EventDispatcher" = field(default_factory=lambda: EventDispatcher())
    # Event sourcing light
    event_log: list["Event"] = field(default_factory=list)
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

    def run_readonly_event(self, root_event: Event) -> list[Event]:
        """
        Ejecuta un evento como simulación:
        - No altera el estado original del GameState
        - Permite que handlers y features modifiquen resultados temporalmente
        """
        shadow_state = deepcopy(self)
        collected: list[Event] = []

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
    def add_token(self, token: dict):
        self.tokens[token["id"]] = token

    def move_token(self, token_id: UUID, x: int, y: int):
        token = self.tokens[token_id]

        if not token:
            raise RuntimeError("Token no existe")
        token["x"] = x
        token["y"] = y


def LongRestEvent(actor_id):
    return Event(
        type="long_rest",
        context=EventContext(actor_id=actor_id),
        cancelable=False
    )

def MoveTokenEvent(token_id: UUID, x: int, y: int):
    return Event(
        type="token_moved",
        payload={"token_id": token_id, "x": x, "y": y},
        cancelable=False
    )
