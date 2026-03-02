from src.core.character.enemy import Enemy, EnemyAttack


def json_to_enemy(data: dict) -> Enemy:
    attacks = [
        EnemyAttack(
            name=atk["name"],
            dice_count=atk["dice_count"],
            dice_size=atk["dice_size"],
            damage_bonus=atk.get("damage_bonus", 0),
            attack_bonus=atk.get("attack_bonus", 0),
            damage_type=atk.get("damage_type", "slashing"),
        )
        for atk in data.get("attacks", [])
    ]

    enemy = Enemy(
        id=data["id"],
        owner_id=data["owner_id"],
        name=data["name"],
        hp=data["hp"],
        max_hp=data["max_hp"],
        ac=data["ac"],
        asset_url=data.get("asset_url"),
        size=(data.get("size_x", 1), data.get("size_y", 1)),
        attributes={
            "STR": data.get("str", 10),
            "DEX": data.get("dex", 10),
            "CON": data.get("con", 10),
            "INT": data.get("int_stat", 10),
            "WIS": data.get("wis", 10),
            "CHA": data.get("cha", 10),
        },
        attacks=attacks,
    )

    return enemy