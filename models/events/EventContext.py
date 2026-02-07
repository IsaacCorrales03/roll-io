from dataclasses import dataclass
from typing import Optional
from uuid import UUID



@dataclass
class EventContext:
    actor_id: Optional[UUID] = None
    target_id: Optional[UUID] = None
    
    turn: Optional[int] = None
    phase: Optional[str] = None
    location_id: Optional[str] = None
    
