from abc import ABC, abstractmethod
from ..events.GameState import GameState
from ..events.Event import Event

class Action(ABC):
    @abstractmethod
    def execute(self, state: GameState) -> Event:
        pass
