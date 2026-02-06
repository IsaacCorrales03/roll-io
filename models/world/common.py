from dataclasses import dataclass
from uuid import UUID
from typing import Dict, Any

@dataclass
class Metadata:
    tags: Dict[str, str]
    extra: Dict[str, Any]
