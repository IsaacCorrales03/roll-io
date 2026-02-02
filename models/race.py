ATTRIBUTE_KEYS = set((
    "STR",
    "DEX",
    "CON",
    "INT",
    "WIS",
    "CHA"
))
BASE_ATTRIBUTES = {
    "STR":10,
    "DEX":10,
    "CON":10,
    "INT":10,
    "WIS":10,
    "CHA":10
}

class Race:
    def __init__(self,name: str,key:str ,description: str, racial_bonus_stats: dict, special_traits: dict):
        self.name = name
        self.key = key
        self.description = description
        self.attributes = BASE_ATTRIBUTES.copy()
        self.racial_bonus_stats = racial_bonus_stats
        for key, bonus in racial_bonus_stats.items():
            if key in self.attributes:
                self.attributes[key] += bonus
        self.special_traits = special_traits or {}
