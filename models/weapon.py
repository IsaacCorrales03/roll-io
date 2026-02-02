class Weapon:
    def __init__(self, name: str, dice_count: int, dice_size: int, attribute: str, bonus: int = 0, damage_type: str = "slashing"):
        self.name = name
        self.dice_count = dice_count
        self.dice_size = dice_size
        self.attribute = attribute
        self.bonus = bonus
        self.damage_type = damage_type
