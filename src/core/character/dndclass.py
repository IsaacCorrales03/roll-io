from abc import ABC
from typing import Dict, List, Type
from ..base import Actor
from .ClassFeature import *


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


class Barbarian(DnDClass):
    name = "Barbaro"
    definition = (
        "Un guerrero feroz impulsado por la furia. "
        "El bárbaro canaliza su ira en combate para obtener "
        "fuerza sobrehumana, resistencia extrema y reflejos salvajes."
    )
    hit_die = 12
    weapon_proficiencies = []
    
    def features_by_level(self) -> dict[int, list[type[ClassFeature]]]:
        return {
            1: [UnarmoredDefense, Rage]
        }

class Bard(DnDClass):
    name = "Bardo"
    definition = (
        "El bardo canaliza la magia a través de la música y las palabras, "
        "inspirando aliados y debilitando enemigos."
    )
    hit_die = 8
    weapon_proficiencies = [
        "simple_weapons", "rapier", "longsword", "shortsword"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod
    def features_by_level(self) -> dict[int, list[type[ClassFeature]]]:
        return {
            2: [SongOfRest]
        }

class Warlock(DnDClass):
    name = "Brujo"
    definition = (
        "Buscadores de conocimiento oculto que obtienen poder mediante "
        "pactos con entidades sobrenaturales."
    )
    hit_die = 8
    weapon_proficiencies = [
        "simple_weapons", "light_crossbow"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Cleric(DnDClass):
    name = "Clérigo"
    definition = (
        "Intermediarios entre el mundo mortal y los planos divinos, "
        "imbuidos de magia sagrada."
    )
    hit_die = 8
    weapon_proficiencies = ["simple_weapons"]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Druid(DnDClass):
    name = "Druida"
    definition = (
        "Encarnaciones vivientes de la voluntad de la naturaleza."
    )
    hit_die = 8
    weapon_proficiencies = ["simple_weapons", "scimitar"]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Ranger(DnDClass):
    name = "Explorador"
    definition = (
        "Guardianes de las fronteras salvajes, expertos en rastreo y combate."
    )
    hit_die = 10
    weapon_proficiencies = [
        "simple_weapons", "martial_weapons", "longbow"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Fighter(DnDClass):
    name = "Guerrero"
    definition = (
        "Maestros absolutos del combate y las armas."
    )
    hit_die = 10
    weapon_proficiencies = [
        "simple_weapons", "martial_weapons"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Sorcerer(DnDClass):
    name = "Hechicero"
    definition = (
        "Canales vivientes de magia innata y peligrosa."
    )
    hit_die = 6
    weapon_proficiencies = ["simple_weapons"]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Wizard(DnDClass):
    name = "Mago"
    definition = (
        "Estudiosos supremos de la magia arcana."
    )
    hit_die = 6
    weapon_proficiencies = ["dagger", "quarterstaff"]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

    def features_by_level(self) -> dict[int, list[type[ClassFeature]]]:
        return {}

class Monk(DnDClass):
    name = "Monje"
    definition = (
        "Guerreros disciplinados que canalizan el ki."
    )
    hit_die = 8
    weapon_proficiencies = ["simple_weapons", "shortsword"]

    def ac_formula(self, actor):
        # Defensa sin armadura del monje
        return 10 + actor.dex_mod + actor.wis_mod

class Paladin(DnDClass):
    name = "Paladin"
    definition = (
        "Guerreros sagrados ligados por juramentos divinos."
    )
    hit_die = 10
    weapon_proficiencies = [
        "simple_weapons", "martial_weapons"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Rogue(DnDClass):
    name = "Picaro"
    definition = (
        "Especialistas en sigilo, astucia y golpes precisos."
    )
    hit_die = 8
    weapon_proficiencies = [
        "simple_weapons", "finesse_weapons", "ranged_weapons"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod


CLASS_MAP: dict[str, Type[DnDClass]] = {
    "Barbaro": Barbarian,
    "Bardo": Bard, 
    "Brujo": Warlock,
    "Clerigo": Cleric, 
    "Druida": Druid,
    "Explorador": Ranger,
    "Guerrero": Fighter, 
    "Hechicero": Sorcerer,
    "Mago": Wizard,
    "Monje": Monk, 
    "Paladin": Paladin,
    "Picaro": Rogue,
}
