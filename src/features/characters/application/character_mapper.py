from src.core.character.character import Character
from src.core.character.race import RACE_MAP
from src.core.character.dndclass import CLASS_MAP

def json_to_character(data: dict) -> Character:
    race = RACE_MAP[data["race_key"]]
    dnd_class = CLASS_MAP[data["class_key"]]

    character = Character.from_dict(
        data=data,
        race=race,
        dnd_class=dnd_class()
    )

    return character
