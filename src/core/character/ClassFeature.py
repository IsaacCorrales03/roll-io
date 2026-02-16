from abc import ABC, abstractmethod
import random
from uuid import UUID

from src.core.base import Actor
from src.core.game.Event import EventContext, Event, GameState
from typing import Optional

class ClassFeature(ABC):
    name: str
    required_level: int
    description: str
    level: int
    type: str
    
    def is_available(self, actor) -> bool:
            return (
                actor.level >= self.required_level
                and self in actor.features
            )
    @abstractmethod
    def on_event(self, event: Event, state: GameState) -> Optional[Event]:
        pass


    @classmethod
    def info(cls) -> dict:
        return {
            "name": cls.name,
            "description": cls.description,
            "level": cls.level
        }
    
class UnarmoredDefense(ClassFeature):
    type = "Pasiva"
    name = "Unarmored Defense"
    description = "Mientras no lleves armadura, tu CA es igual a 10 + tu modificador de Destreza + tu modificador de Constitución."
    level = 1
    required_level = 1
    def on_event(self, event: Event, state: GameState) -> Optional[Event]:
        if event.type != "ac_requested":
            return None

        ctx = event.context
        if ctx is None:
            return None

        actor_id = ctx.actor_id
        if actor_id is None:
            return None

        actor = state.characters.get(actor_id)
        if actor is None:
            return None

        # Condición: sin armadura
        if actor.armor is not None:
            return None

        ac = 10 + actor.dex_mod + actor.con_mod
        return Event(
            type="ac_base_calculated",
            context=ctx,
            payload={
                "source": self.name,
                "value": ac
            },
            cancelable=False
        )

class Rage(ClassFeature):
    name = "Rage"
    type = "Activa"
    description = "En combate, puedes entrar en un estado de furia que te otorga ventajas y habilidades especiales, pero solo puedes usarlo un número limitado de veces."
    required_level = 1
    level = 1
    RAGE_DURATION_TURNS = 3 

    def on_event(self, event: Event, state: GameState) -> Optional[Event]:
        if event.type != "rage_requested":
            return None

        ctx = event.context
        if ctx is None or ctx.actor_id is None:
            return None

        actor = state.characters.get(ctx.actor_id)
        if actor is None:
            return None

        resources = state.resources.get(actor.id, {})
        uses = resources.get("rage_uses", 0)

        # Validación
        if uses <= 0:
            return Event(
                type="rage_failed",
                context=ctx,
                payload={"reason": "No uses left"},
                cancelable=False
            )

        # Consumir recurso
        resources["rage_uses"] = uses - 1

        # Aplicar estado
        actor.status["rage"] = {
            "turns": self.RAGE_DURATION_TURNS,
            "bonus": resources.get("rage_bonus", 0)
        }

        return Event(
            type="rage_started",
            context=ctx,
            payload={
                "turns": self.RAGE_DURATION_TURNS,
                "bonus": resources.get("rage_bonus", 0)
            },
            cancelable=False
        )
class SongOfRest(ClassFeature):
    type = "Activa"
    # Metadatos de la feature
    name = "SongOfRest"
    description = (
        "Durante un breve descanso, puedes usar música o palabras motivadoras "
        "para curar a los aliados cercanos un dado de golpe extra."
    )
    required_level = 2  # nivel mínimo del personaje para desbloquear
    level: int = 1  # se actualizará al nivel del actor

    # Mapping nivel -> dado de curación
    LEVEL_DIE_MAP = {
        2: 6,
        9: 8,
        13: 10,
        17: 12
    }
    def on_event(self, event: Event, state: GameState) -> Event | None:
        return super().on_event(event, state)

    @property
    def die(self) -> int:
        # Escalar el dado según el nivel del personaje
        for lvl in sorted(self.LEVEL_DIE_MAP.keys(), reverse=True):
            if self.level >= lvl:
                return self.LEVEL_DIE_MAP[lvl]
    
        return 0  # si el personaje no tiene el nivel requerido

    def use(self, actor: Actor, state: GameState, **kwargs) -> Event:
        if actor.level < self.required_level:
            return Event(
                type="song_of_rest_failed",
                context=EventContext(actor_id=actor.id),
                payload={"reason": "Nivel insuficiente"},
                cancelable=False
            )

        targets: list[UUID] = kwargs.get("targets", [])
        healed = []

        for t in targets:
            target_actor = state.characters.get(t)
            if target_actor is None:
                continue
            amount = random.randint(1, self.die)  # dado según level
            target_actor.hp = min(target_actor.max_hp, target_actor.hp + amount)
            healed.append({"target": t, "amount": amount})

        return Event(
            type="song_of_rest_used",
            context=EventContext(actor_id=actor.id),
            payload={"healed": healed},
            cancelable=False
        )

