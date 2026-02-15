import uuid
from typing import Optional

from models.character import Character
from models.races import RACE_MAP
from models.dndclasses import CLASS_MAP
from services.character_repository import CharacterRepository
from services.character_mapper import json_to_character


class CharacterService:
    def __init__(self, repo: CharacterRepository):
        self.repo = repo

    def create(self, owner_id: uuid.UUID, name: str, race_key: str, class_key: str, token_texture = None) -> Character:
        character = Character(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=name,
            race=RACE_MAP[race_key],
            dnd_class=CLASS_MAP[class_key]()
        )
        if token_texture:
            character.token_texture = token_texture
        else:
            character.token_texture = f"imgs/{class_key}.jpg" # type: ignore
        self.repo.create(character.to_json(), owner_id, token_texture)
        return character

    def load(self, from_id: str) -> Optional[Character]:
        data = self.repo.get_by_id(from_id)
        if data is None:
            return None
        return json_to_character(data)
