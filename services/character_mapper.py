from models.character import Character
from models.races import RACE_MAP
from models.dndclasses import CLASS_MAP
import uuid


def json_to_character(data: dict) -> Character:
    race = RACE_MAP[data["race_key"]]
    dnd_class = CLASS_MAP[data["class_key"]]

    character = Character.from_dict(
        data=data,
        race=race,
        dnd_class=dnd_class()
    )

    return character
