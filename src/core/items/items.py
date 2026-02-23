from src.core.items.item import Armor, Item, Shield, Weapon
# Claves únicas estables (no cambiarlas luego)
HEAL_POTION = "heal_potion"
LONG_SWORD = "long_sword"
IRON_ARMOR = "iron_armor"
WOOD_SHIELD = "wood_shield"


ITEMS: dict[str, Item] = {

    HEAL_POTION: Item(
        item_id=HEAL_POTION,
        name="Healing Potion",
        weight=0.5,
        stackable=True,
        description="Restores 2d4 + 2 HP when consumed.",
        item_type="consumable",
    ),

    LONG_SWORD: Weapon(
        item_id=LONG_SWORD,
        name="Long Sword",
        weight=3.0,
        dice_count=1,
        dice_size="1d8",
        attribute="STR",
        description="A versatile melee weapon that can be used with one or two hands.",
    ),

    IRON_ARMOR: Armor(
        item_id=IRON_ARMOR,
        name="Iron Armor",
        description="Heavy armor that provides excellent protection but imposes disadvantage on Stealth checks.",
        weight=30.0,
        base_ac=16,
        dex_bonus=False,
        dex_bonus_limit=None,
        stealth_disadvantage=True,
    ),

    WOOD_SHIELD: Shield(
        item_id=WOOD_SHIELD,
        name="Wood Shield",
        description="A sturdy wooden shield that provides a +2 bonus to AC when equipped.",
        weight=6.0,
        ac_bonus=2,
    ),
}
