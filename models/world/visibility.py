from dataclasses import dataclass
from typing import List

@dataclass
class VisibilityRule:
    default: str  # "hidden" | "fogged" | "visible"
    revealed_by: List[str]  # condiciones evaluables
