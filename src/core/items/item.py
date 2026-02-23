import uuid

class Item:
    def __init__(
        self,
        item_id: str,
        name: str,
        description: str,
        item_type: str,
        weight: float,
        stackable: bool,
        max_stack: int = 1,
    ):
        self.item_id = item_id
        self.name = name
        self.item_type = item_type
        self.weight = weight
        self.description = description
        self.stackable = stackable
        self.max_stack = max_stack

class ItemInstance:
    def __init__(
        self,
        item: Item,
        quantity: int = 1,
        durability: int | None = None,
        equipped: bool = False
    ):
        self.instance_id = str(uuid.uuid4())
        self.item = item
        self.quantity = quantity
        self.durability = durability
        self.equipped = equipped
    def is_stackable(self) -> bool:
        return self.item.stackable
    
class Weapon(Item):
    def __init__(self,item_id: str,
                 name: str,
                 description: str,
                 weight: float,
                 dice_count: int,
                 dice_size: str,
                 attribute: str,
                 bonus: int = 0,
                 range: int = 5, 
                 long_range: int | None = None,
                 damage_type: str = "slashing"):
        super().__init__(
            item_id=item_id,
            name=name,
            description=description,
            weight=weight,
            item_type="weapon",
            stackable=False  # Las armas no se apilan
        )

        # Cantidad de dados de daño (ej. 2d6 → dice_count = 2)
        self.dice_count = dice_count

        # Tamaño del dado de daño (ej. d6, d8, d12)
        self.dice_size = dice_size

        # Atributo usado para atacar y dañar (STR o DEX)
        self.attribute = attribute

        # Bonificador fijo al daño
        self.bonus = bonus

        # Tipo de daño (slashing, piercing, bludgeoning, etc.)
        self.damage_type = damage_type
        # Alcance en pies
        self.range = range
        self.long_range = long_range

class Armor(Item):
    def __init__(
        self,
        item_id: str,
        name: str,
        description: str,
        weight: float,
        base_ac: int,
        dex_bonus: bool = True,
        dex_bonus_limit: int | None = None,
        stealth_disadvantage: bool = False
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            description=description,
            item_type="armor",
            weight=weight,
            stackable=False
        )

        # AC base que otorga la armadura
        self.base_ac = base_ac

        # Si permite sumar modificador de DEX
        self.dex_bonus = dex_bonus

        # Límite máximo de DEX que puede sumarse (ej: armaduras medias)
        self.dex_bonus_limit = dex_bonus_limit

        # Si impone desventaja en sigilo
        self.stealth_disadvantage = stealth_disadvantage

class Shield(Item):
    def __init__(
        self,
        item_id: str,
        name: str,
        description: str,
        weight: float,
        ac_bonus: int = 2
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            description=description,
            item_type="shield",
            weight=weight,
            stackable=False
        )

        # Bono fijo a la AC
        self.ac_bonus = ac_bonus
