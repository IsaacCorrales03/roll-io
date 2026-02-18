from uuid import uuid4


class Enemy:
    def __init__(self, id, name, hp, max_hp, ac, asset_url, size=(1, 1)):
        self.id = id
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.ac = ac
        self.size = size
        self.asset_url = asset_url

    def to_dict(self):  
        return {
            "id": str(self.id),
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "ac": self.ac,
            "asset_url": self.asset_url
        }

  