class Weapon:
    def __init__(
        self,
        name: str,
        dice_count: int,
        dice_size: int,
        attribute: str,
        bonus: int = 0,
        damage_type: str = "slashing"
    ):
        # Nombre visible del arma
        self.name = name

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
