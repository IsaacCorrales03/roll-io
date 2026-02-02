from .base import Actor, ClassFeature
from abc import ABC, abstractmethod

class DnDClass(ABC):
    name: str
    definition: str
    hit_die: int
    weapon_proficiencies: list

    @abstractmethod
    def ac_formula(self, actor) -> int:
        """
        Devuelve la AC base cuando NO hay armadura equipada.
        """
        pass

    def features_by_level(self) -> dict[int, list[type[ClassFeature]]]:
        return {}
    
    def features_info_by_level(self) -> dict[int, list[dict]]:
        return {
            level: [feature.info() for feature in features]
            for level, features in self.features_by_level().items()
        }