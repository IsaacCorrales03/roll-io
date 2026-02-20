from src.core.items.item import ItemInstance
from src.core.character.character import Character
from src.core.character.dndclass import CLASS_MAP
from src.core.character.race import RACE_MAP
from src.core.items.items import ITEMS
import uuid

test = Character(
    id=uuid.uuid4(),
    owner_id=uuid.uuid4(),
    name="Test Character",
    race=RACE_MAP["Human"],
    dnd_class=CLASS_MAP["Mago"](),
)
item = ITEMS["long_sword"]
instance = ItemInstance(
    item=item,
    quantity=1
)
test.add_item(instance)

for item in test.inventory:
    print(f"{item.item.name} x{item.quantity}")
print(test.to_json()["inventory"])