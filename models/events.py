from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from uuid import UUID, uuid4
from collections import defaultdict
from abc import ABC, abstractmethod
from copy import deepcopy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .character import Character

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


class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: "Event", state: "GameState") -> None:
        pass

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



@dataclass(frozen=True)
class ActionContext:
    actor_id: Optional[str]
    target_id: Optional[str]

    turn: Optional[int]
    phase: Optional[str]        # exploration | combat | rest | dialogue

    location_id: Optional[str]
    combat_id: Optional[str]

class RollResult:
    def __init__(self, base: int):
        self.base = base
        self.modifiers: list[int] = []

    def add_modifier(self, value: int):
        self.modifiers.append(value)

    @property
    def total(self) -> int:
        return self.base + sum(self.modifiers)

@dataclass
class GameState:
    characters: Dict[UUID, "Character"] = field(default_factory=dict)

    # Flujo global
    current_turn: Optional[int] = None
    current_actor: Optional[UUID] = None
    current_phase: Optional[str] = None  # combat | exploration | rest | dialogue

    # Orden de iniciativa (solo relevante en combate)
    initiative_order: List[UUID] = field(default_factory=list)
    dispatcher: "EventDispatcher" = field(default_factory=lambda: EventDispatcher())
    # Event sourcing light
    event_log: List["Event"] = field(default_factory=list)
    _handlers: dict = field(default_factory=dict)

    def register_handler(self, event_type: str, handler: EventHandler):
        self._handlers.setdefault(event_type, []).append(handler)

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
