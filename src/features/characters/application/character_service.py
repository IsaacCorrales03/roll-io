import uuid
from typing import Optional

from src.core.items.items import ITEMS
from src.core.items.item import ItemInstance
from src.core.character.character import Character
from src.core.character.race import RACE_MAP
from src.core.character.dndclass import CLASS_MAP
from src.features.characters.infrastructure.character_repository import CharacterRepository
from src.features.characters.application.character_mapper import json_to_character


class CharacterService:
    def __init__(self, repo: CharacterRepository):
        self.repo = repo

    def create(self, owner_id: uuid.UUID, name: str, race_key: str, class_key: str, chosen_skills: list[str], token_texture = None, ) -> Character:
        dnd_class = CLASS_MAP[class_key]()
        character = Character(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=name,
            race=RACE_MAP[race_key],
            dnd_class=dnd_class
        )
        if token_texture:
            character.texture = token_texture
        else:
            character.texture = f"imgs/{class_key}.jpg" # type: ignore
        dnd_class.grant_proficiencies(
            character,
            chosen_skills=chosen_skills
        )
        dnd_class.grant_features(character)
        
        self.repo.create(character.to_json(), owner_id, token_texture)
        self.repo.save_inventory(str(character.id), {})
        return character
        
    def save(self, character: Character):
        data = character.to_json()
        self.repo.save(data, character.owner_id)

        inventory_dict: dict[str, dict] = {}

        for instance in character.inventory:
            iid = instance.item.item_id

            if iid not in inventory_dict:
                inventory_dict[iid] = {
                    "quantity": 0,
                    "equipped": False
                }

            inventory_dict[iid]["quantity"] += instance.quantity

            # Si alguna instancia está equipada → marcar
            if getattr(instance, "equipped", False):
                inventory_dict[iid]["equipped"] = True

        self.repo.save_inventory(str(character.id), inventory_dict)

        
    def load(self, from_id: str) -> Optional[Character]:
        data = self.repo.get_by_id(from_id)
        if data is None:
            return None

        proficiencies = self.repo.get_proficiencies(from_id)
        data.update(proficiencies)

        character = json_to_character(data)

        inventory_rows = self.repo.get_inventory(from_id)
        character.load_inventory(inventory_rows)

        return character