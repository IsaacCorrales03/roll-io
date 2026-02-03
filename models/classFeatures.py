from .base import Actor
from .ClassFeature import ClassFeature as ClassFeature
from typing import Optional
import random
from .events import Event, GameState, EventContext
from uuid import UUID

class UnarmoredDefense(ClassFeature):
    name = "Unarmored Defense"

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


class SongOfRest(ClassFeature):
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

