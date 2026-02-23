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
    advantage: bool
    disadvantage: bool
    attack_name: str = "attack"

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

@dataclass(frozen=True)
class StatusCommand:
    actor_id: UUID
    target_id: UUID
    status: str
    duration_turns: int = 1

@dataclass(frozen=True)
class CreateEnemyCommand:
    name:str
    max_hp: int
    hp: int
    ac: int
    asset_url: str
    size: tuple

@dataclass(frozen=True)
class MoveCommand:
    actor_id: UUID
    from_position: tuple[int, int]
    to_position: tuple[int, int]
@dataclass(frozen=True)
class StartCombatCommand:
    participant_ids: list[UUID]


@dataclass(frozen=True)
class EndTurnCommand:
    actor_id: UUID