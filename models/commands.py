from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class RollCommand:
    actor_id: UUID           
    dice: str                
    reason: str           
    advantage: bool = False
    disadvantage: bool = False

@dataclass(frozen=True)
class AttackCommand:
    actor_id: UUID
    target_id: UUID
    mode: str
    adventage: bool
    disadventage: bool

@dataclass(frozen=True)
class UseBardicInspirationCommand:
    source_id: UUID   # el bardo
    target_id: UUID   # el inspirado

@dataclass(frozen=True)
class GetArmorClassCommand:
    actor_id: UUID
    context: str  # ej: "attack_resolution", "ui_preview"

@dataclass(frozen=True)
class UseRageCommand:
    actor_id: UUID
    
@dataclass(frozen=True)
class UseSongOfRestCommand:
    actor_id: UUID
    targets: list[UUID]  # opcional: a quién afecta

class StatusCommand:
    def __init__(self, actor_id: UUID, target_id: UUID, status: str, duration_turns: int = 1):
        self.actor_id = actor_id       # quien aplica el estado
        self.target_id = target_id     # quien recibe el estado
        self.status = status           # el nombre del estado
        self.duration_turns = duration_turns
