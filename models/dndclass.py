from abc import ABC
from typing import Dict, List, Type
from .base import Actor
from .ClassFeature import ClassFeature


class DnDClass(ABC):
    # Metadatos
    name: str
    definition: str
    hit_die: int
    weapon_proficiencies: list

    # =======================
    # Declaración de features
    # =======================
    def features_by_level(self) -> Dict[int, List[Type[ClassFeature]]]:
        """
        Mapa: nivel -> lista de clases de ClassFeature
        Ej:
        {
            1: [UnarmoredDefense],
            2: [RecklessAttack]
        }
        """
        return {}

    # =======================
    # Asignación al Actor
    # =======================
    def grant_features(self, actor: Actor) -> None:
        """
        Otorga al actor todas las features correspondientes
        a su nivel actual. Idempotente.
        """
        for level, feature_classes in self.features_by_level().items():
            if actor.level < level:
                continue

            for feature_cls in feature_classes:
                if not any(isinstance(f, feature_cls) for f in actor.features):
                    actor.features.append(feature_cls())

    # =======================
    # Serialización (UI / API)
    # =======================
    def features_info_by_level(self) -> Dict[int, List[dict]]:
        return {
            level: [feature_cls.info() for feature_cls in features]
            for level, features in self.features_by_level().items()
        }
