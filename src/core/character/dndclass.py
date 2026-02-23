from abc import ABC
from typing import Dict, List, Type
from ..base import Actor
from .ClassFeature import *


from abc import ABC, abstractmethod
from typing import Dict, List, Type
from ..base import Actor
from .ClassFeature import ClassFeature


class DnDClass(ABC):
    # =======================
    # Metadatos obligatorios
    # =======================
    name: str
    definition: str
    hit_die: int

    # =======================
    # Competencias base
    # =======================
    skill_choices: list[str] = []
    skill_choices_count: int = 0
    saving_throw_proficiencies: list[str] = []
    weapon_proficiencies: list[str] = []
    armor_proficiencies: list[str] = []

    # =======================
    # Features por nivel
    # =======================
    def features_by_level(self) -> Dict[int, List[Type[ClassFeature]]]:
        return {}

    # =======================
    # Aplicación de competencias
    # =======================
    def grant_proficiencies(
        self,
        actor: Actor,
        chosen_skills: list[str] | None = None
    ) -> None:

        # Salvaciones
        actor.saving_throw_proficiencies.update(
            self.saving_throw_proficiencies
        )

        # Armas
        actor.weapon_proficiencies.update(
            self.weapon_proficiencies
        )

        # Armaduras
        actor.armor_proficiencies.update(
            self.armor_proficiencies
        )

        # Skills elegidas
        if self.skill_choices_count > 0:
            if not chosen_skills:
                raise ValueError("Skill choices required")

            if len(chosen_skills) != self.skill_choices_count:
                raise ValueError("Invalid number of skill choices")

            for skill in chosen_skills:
                if skill not in self.skill_choices:
                    raise ValueError(f"{skill} not allowed")

            actor.skill_proficiencies.update(chosen_skills)

    # =======================
    # Aplicación de features
    # =======================
    def grant_features(self, actor: Actor) -> None:
        for level, feature_classes in self.features_by_level().items():
            if actor.level < level:
                continue

            for feature_cls in feature_classes:
                if not any(isinstance(f, feature_cls) for f in actor.features):
                    actor.features.append(feature_cls())


    # =======================
    # Serialización
    # =======================
    def features_info_by_level(self) -> Dict[int, List[dict]]:
        return {
            level: [feature_cls.info() for feature_cls in features]
            for level, features in self.features_by_level().items()
        }

class Barbarian(DnDClass):
    name = "Barbaro"
    definition = (
        "Guerrero feroz impulsado por la furia."
    )
    hit_die = 12

    # =======================
    # Competencias
    # =======================
    skill_choices = [
        "athletics",
        "intimidation",
        "nature",
        "perception",
        "survival",
        "animal_handling"
    ]
    skill_choices_count = 2

    saving_throw_proficiencies = [
        "strength",
        "constitution"
    ]

    weapon_proficiencies = [
        "simple_weapons",
        "martial_weapons"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "shields"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod
    # =======================
    # Features por nivel
    # =======================
    def features_by_level(self):
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
    skill_choices = [
        "acrobatics",
        "animal_handling",
        "arcana",
        "athletics",
        "deception",
        "history",
        "insight",
        "intimidation",
        "investigation",
        "medicine",
        "nature",
        "perception",
        "performance",
        "persuasion",
        "religion",
        "sleight_of_hand",
        "stealth",
        "survival"
    ]
    saving_throw_proficiencies = [
    "dexterity",
    "charisma"
    ]

    weapon_proficiencies = [
        "simple_weapons",
        "shortsword",
        "longsword",
        "rapier",
        "hand_crossbow"
    ]

    armor_proficiencies = [
        "light_armor"
    ]
    skill_choices_count = 3

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
    saving_throw_proficiencies = [
        "wisdom",
        "charisma"
    ]

    skill_choices = [
        "arcana",
        "deception",
        "history",
        "intimidation",
        "investigation",
        "nature",
        "religion"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "simple_weapons"
    ]

    armor_proficiencies = [
        "light_armor"
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
    saving_throw_proficiencies = [
        "wisdom",
        "charisma"
    ]

    skill_choices = [
        "history",
        "medicine",
        "insight",
        "persuasion",
        "religion"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "simple_weapons"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "shields"
    ]
    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Druid(DnDClass):
    name = "Druida"
    definition = (
        "Encarnaciones vivientes de la voluntad de la naturaleza."
    )
    hit_die = 8
    saving_throw_proficiencies = [
        "intelligence",
        "wisdom"
    ]

    skill_choices = [
        "arcana",
        "medicine",
        "nature",
        "perception",
        "insight",
        "religion",
        "survival",
        "animal_handling"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "club",
        "dagger",
        "dart",
        "javelin",
        "mace",
        "quarterstaff",
        "scimitar",
        "sickle",
        "sling",
        "spear"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "shields"
    ]


    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Ranger(DnDClass):
    name = "Explorador"
    definition = (
        "Guardianes de las fronteras salvajes, expertos en rastreo y combate."
    )
    hit_die = 10
    # =======================
    # Competencias
    # =======================   

    saving_throw_proficiencies = [
        "strength",
        "dexterity"
    ]

    skill_choices = [
        "athletics",
        "investigation",
        "nature",
        "perception",
        "insight",
        "stealth",
        "survival",
        "animal_handling"
    ]

    skill_choices_count = 3

    weapon_proficiencies = [
        "simple_weapons",
        "martial_weapons"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "shields"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Fighter(DnDClass):
    name = "Guerrero"
    definition = (
        "Maestros absolutos del combate y las armas."
    )
    hit_die = 10
    # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "strength",
        "constitution"
    ]

    skill_choices = [
        "acrobatics",
        "athletics",
        "history",
        "intimidation",
        "perception",
        "insight",
        "survival",
        "animal_handling"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "simple_weapons",
        "martial_weapons"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "heavy_armor",
        "shields"
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Sorcerer(DnDClass):
    name = "Hechicero"
    definition = (
        "Canales vivientes de magia innata y peligrosa."
    )
    hit_die = 6
        # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "constitution",
        "charisma"
    ]

    skill_choices = [
        "arcana",
        "deception",
        "intimidation",
        "insight",
        "persuasion",
        "religion"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "dagger",
        "dart",
        "sling",
        "quarterstaff",
        "light_crossbow"
    ]

    armor_proficiencies = [
    ]

    def ac_formula(self, actor):
        return 10 + actor.dex_mod

class Wizard(DnDClass):
    name = "Mago"
    definition = (
        "Estudiosos supremos de la magia arcana."
    )
    hit_die = 6
    # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "intelligence",
        "wisdom"
    ]

    skill_choices = [
        "arcana",
        "history",
        "investigation",
        "medicine",
        "insight",
        "religion"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "dagger",
        "dart",
        "sling",
        "quarterstaff",
        "light_crossbow"
    ]

    armor_proficiencies = [
    ]

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
        # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "strength",
        "dexterity"
    ]

    skill_choices = [
        "acrobatics",
        "athletics",
        "history",
        "insight",
        "religion",
        "stealth"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "simple_weapons",
        "shortsword"
    ]

    armor_proficiencies = [
    ]


    def ac_formula(self, actor):
        # Defensa sin armadura del monje
        return 10 + actor.dex_mod + actor.wis_mod

class Paladin(DnDClass):
    name = "Paladin"
    definition = (
        "Guerreros sagrados ligados por juramentos divinos."
    )
    hit_die = 10
        # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "wisdom",
        "charisma"
    ]

    skill_choices = [
        "athletics",
        "intimidation",
        "medicine",
        "insight",
        "persuasion",
        "religion"
    ]

    skill_choices_count = 2

    weapon_proficiencies = [
        "simple_weapons",
        "martial_weapons"
    ]

    armor_proficiencies = [
        "light_armor",
        "medium_armor",
        "heavy_armor",
        "shields"
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
        # =======================
    # Competencias
    # =======================

    saving_throw_proficiencies = [
        "dexterity",
        "intelligence"
    ]

    skill_choices = [
        "acrobatics",
        "athletics",
        "deception",
        "performance",
        "intimidation",
        "investigation",
        "sleight_of_hand",
        "perception",
        "insight",
        "persuasion",
        "stealth"
    ]

    skill_choices_count = 4

    weapon_proficiencies = [
        "simple_weapons",
        "hand_crossbow",
        "longsword",
        "rapier",
        "shortsword"
    ]

    armor_proficiencies = [
        "light_armor"
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
