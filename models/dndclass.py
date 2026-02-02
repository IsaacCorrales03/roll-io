from .base import Actor, ClassFeature
from abc import ABC, abstractmethod


class DnDClass(ABC):
    # Nombre visible de la clase (ej. Bárbaro, Guerrero)
    name: str

    # Descripción narrativa de la clase
    definition: str

    # Dado de golpe usado para calcular HP
    hit_die: int

    # Lista de armas con las que la clase es competente
    weapon_proficiencies: list

    @abstractmethod
    def ac_formula(self, actor) -> int:
        """
        Calcula la Clase de Armadura base del personaje
        cuando NO lleva armadura equipada.
        Cada clase define su propia fórmula.
        """
        pass

    def features_by_level(self) -> dict[int, list[type[ClassFeature]]]:
        """
        Devuelve las habilidades de clase agrupadas por nivel.
        La clave es el nivel, el valor son las clases de features.
        """
        return {}

    def features_info_by_level(self) -> dict[int, list[dict]]:
        """
        Versión serializable de las habilidades por nivel.
        Útil para exponer datos al frontend o a la API.
        """
        return {
            level: [feature.info() for feature in features]
            for level, features in self.features_by_level().items()
        }
