from abc import ABC, abstractmethod
from .events.Event import Event
from .events.GameState import GameState
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