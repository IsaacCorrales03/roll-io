from typing import Dict, TypeVar, Mapping, overload, Iterable, Any
from uuid import UUID

from .world import World
from .region import Region
from .location import Location
from .route import Route
from .poi import PointOfInterest
from .faction import Faction
from .npc import NPC
from .exceptions import EntityNotFound, InvalidReference, UnknownEntityType


T = TypeVar("T", Region, Location, Route, PointOfInterest, Faction, NPC)


class WorldRegistry:
    def __init__(self, world: World):
        self.world = world

        self.regions: Dict[UUID, Region] = {}
        self.locations: Dict[UUID, Location] = {}
        self.routes: Dict[UUID, Route] = {}
        self.pois: Dict[UUID, PointOfInterest] = {}
        self.factions: Dict[UUID, Faction] = {}
        self.npcs: Dict[UUID, NPC] = {}

    # ---------- REGISTRO ----------
    def add(self, entity: object) -> None:
        if isinstance(entity, Region):
            self.regions[entity.id] = entity
        elif isinstance(entity, Location):
            self.locations[entity.id] = entity
        elif isinstance(entity, Route):
            self.routes[entity.id] = entity
        elif isinstance(entity, PointOfInterest):
            self.pois[entity.id] = entity
        elif isinstance(entity, Faction):
            self.factions[entity.id] = entity
        elif isinstance(entity, NPC):
            self.npcs[entity.id] = entity
        else:
            raise TypeError(f"Unknown entity type: {type(entity)}")

    # ---------- ACCESO ----------
    def get(self, entity_type: type[T], entity_id: UUID) -> T:
        store = self._store_for(entity_type)
        try:
            return store[entity_id]  # type: ignore[index]
        except KeyError:
            raise EntityNotFound(entity_type.__name__, entity_id)

    # ---------- STORE INTERNO ----------
    @overload
    def _store_for(self, entity_type: type[Region]) -> Mapping[UUID, Region]: ...
    @overload
    def _store_for(self, entity_type: type[Location]) -> Mapping[UUID, Location]: ...
    @overload
    def _store_for(self, entity_type: type[Route]) -> Mapping[UUID, Route]: ...
    @overload
    def _store_for(self, entity_type: type[PointOfInterest]) -> Mapping[UUID, PointOfInterest]: ...
    @overload
    def _store_for(self, entity_type: type[Faction]) -> Mapping[UUID, Faction]: ...
    @overload
    def _store_for(self, entity_type: type[NPC]) -> Mapping[UUID, NPC]: ...

    def _store_for(self, entity_type: type[Any]) -> Mapping[UUID, object]:
        if entity_type is Region:
            return self.regions
        if entity_type is Location:
            return self.locations
        if entity_type is Route:
            return self.routes
        if entity_type is PointOfInterest:
            return self.pois
        if entity_type is Faction:
            return self.factions
        if entity_type is NPC:
            return self.npcs

        raise UnknownEntityType(f"Unsupported entity type: {entity_type}")

    # ---------- VALIDACIÓN ----------
    def validate(self) -> None:
        for loc in self.locations.values():
            if loc.region not in self.regions:
                raise InvalidReference(f"Location {loc.id} -> region {loc.region}")

            for child in loc.children:
                if child not in self.locations:
                    raise InvalidReference(f"Location {loc.id} -> child {child}")

        for route in self.routes.values():
            if route.from_location not in self.locations:
                raise InvalidReference(f"Route {route.id} from invalid location")
            if route.to_location not in self.locations:
                raise InvalidReference(f"Route {route.id} to invalid location")

        for poi in self.pois.values():
            if poi.location not in self.locations:
                raise InvalidReference(f"POI {poi.id} -> location {poi.location}")

        for npc in self.npcs.values():
            if npc.current_location not in self.locations:
                raise InvalidReference(f"NPC {npc.id} -> location {npc.current_location}")

    # ---------- ITERADORES ----------
    def all_locations(self) -> Iterable[Location]:
        return self.locations.values()
