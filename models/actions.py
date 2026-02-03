import random
from .events import EventDispatcher, RollResult, EventContext, Event, GameState
from abc import ABC, abstractmethod
from .commands import *

import random

def roll_dice(dice: str) -> int:
    count, die = dice.lower().split("d")
    return sum(random.randint(1, int(die)) for _ in range(int(count)))


class Action(ABC):
    @abstractmethod
    def execute(self, state: GameState) -> Event:
        pass


class UseSongOfRestAction(Action):
    def __init__(self, command: UseSongOfRestCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:
        actor = state.characters[self.command.actor_id]
        # La feature activa contiene la lógica
        song = actor.get_feature("SongOfRest")  # búsqueda por nombre
        if song:
            return song.use(actor, state, targets=self.command.targets)
        else: 
            return Event(
                type="song_of_rest_failed",
                context=EventContext(actor_id=actor.id),
                payload={"reason": "Habilidad no aprendida"},
                cancelable=False
            )



class RollAction(Action):
    def __init__(self, command: RollCommand):
        self.command = command

    def execute(self, state: GameState) -> Event:
        value = roll_dice(self.command.dice)

        context = EventContext(
            actor_id=self.command.actor_id,
            turn=state.current_turn,
            phase=state.current_phase,
        )

        return Event(
            type="roll_result",
            source="engine",
            context=context,
            payload={
                "dice": self.command.dice,
                "value": value,
                "reason": self.command.reason,
            },
            cancelable=True,
        )