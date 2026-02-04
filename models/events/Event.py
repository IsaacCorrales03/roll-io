from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4, UUID
from typing import Optional, Dict, Any
from models.events.EventContext import EventContext

@dataclass(frozen=True)
class Event:
    id: UUID = field(default_factory=uuid4)
    type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    context: Optional["EventContext"] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    cancelable: bool = False
