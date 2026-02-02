from models.character import Character
from models.races import RACE_MAP
from models.dndclasses import CLASS_MAP


def json_to_character(data: dict) -> Character:
    character = Character(
        id=data["id"],
        name=data["name"],
        race=RACE_MAP[data["race_key"]],
        dnd_class=CLASS_MAP[data["class_key"]]()
    )

    character.level = data["level"]

    character.hp = data["hp"]

    return character
