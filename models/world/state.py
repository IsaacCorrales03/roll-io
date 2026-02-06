from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class StateBlock:
    flags: Dict[str, bool] = field(default_factory=dict)
    values: Dict[str, Any] = field(default_factory=dict)
    effects: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
