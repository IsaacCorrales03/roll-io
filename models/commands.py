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
class UseSongOfRestCommand:
    actor_id: UUID
    targets: list[UUID]  # opcional: a quién afecta
