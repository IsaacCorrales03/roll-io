from uuid import UUID
from typing import List

from .registry import WorldRegistry
from .location import Location


def locations_in_region(registry: WorldRegistry, region_id: UUID) -> List[Location]:
    return [
        loc for loc in registry.locations.values()
        if loc.region == region_id
    ]


def child_locations(registry: WorldRegistry, parent_id: UUID) -> List[Location]:
    return [
        registry.locations[child_id]
        for child_id in registry.locations[parent_id].children
    ]


def routes_from_location(registry: WorldRegistry, location_id: UUID):
    return [
        route for route in registry.routes.values()
        if route.from_location == location_id
    ]
