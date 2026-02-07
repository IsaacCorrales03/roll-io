# models/world/WorldState.py
from dataclasses import dataclass, field
from typing import Dict
from uuid import UUID
from .region import Region
from .location import Location
from .poi import PointOfInterest
from .faction import Faction
from .npc import NPC

@dataclass
class WorldState:
    regions: Dict[UUID, Region] = field(default_factory=dict)
    locations: Dict[UUID, Location] = field(default_factory=dict)
    pois: Dict[UUID, PointOfInterest] = field(default_factory=dict)
    factions: Dict[UUID, Faction] = field(default_factory=dict)
    npcs: Dict[UUID, NPC] = field(default_factory=dict)
