from src.core.items.item import ItemInstance
from src.core.items.items import ITEMS

# Convertimos los items a instancias de ItemInstance
item_instances = [
    ItemInstance(item) for item in ITEMS.values()
]

def serialize_item_instance(instance: ItemInstance) -> dict:
    return {
        "instance_id": instance.instance_id,
        "item_id": instance.item.item_id,
        "quantity": instance.quantity,
        "durability": instance.durability,
        "equipped": instance.equipped,
        "meta": {
            "name": instance.item.name,
            "description": instance.item.description,
            "item_type": instance.item.item_type,
            "weight": instance.item.weight
        }
    }