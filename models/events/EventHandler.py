from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Event import Event
    from .GameState import GameState

class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: "Event", state: "GameState") -> None:
        pass