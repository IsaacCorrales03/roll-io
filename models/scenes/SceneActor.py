from dataclasses import dataclass
from uuid import UUID
from typing import Literal, Optional

ActorKind = Literal["character", "npc", "enemy"]

@dataclass
class SceneActor:
    actor_id: UUID              # ID del Actor real (Character, NPC, Enemy)
    kind: ActorKind
    section_id: str             # a1, b2, etc
    visible: bool = True        # override puntual (no fog global)
