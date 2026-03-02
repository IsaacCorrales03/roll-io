import uuid
from typing import Optional, List

from src.core.character.enemy import Enemy, EnemyAttack
from src.features.enemies.infrastructure.enemy_repository import EnemyRepository
from src.features.enemies.application.enemy_mapper import json_to_enemy


class EnemyService:
    def __init__(self, repo: EnemyRepository):
        self.repo = repo

    # =========================
    # CREATE
    # =========================
    def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        hp: int,
        max_hp: int,
        ac: int,
        attributes: dict[str, int],
        attacks: List[dict],
        asset_url: str | None = None,
        size: tuple[int, int] = (1, 1),
    ) -> Enemy:

        enemy = Enemy(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=name,
            hp=hp,
            max_hp=max_hp,
            ac=ac,
            asset_url=asset_url,
            size=size,
            attributes=attributes,
            attacks=[
                EnemyAttack(**attack_dict)
                for attack_dict in attacks
            ],
        )

        self.repo.create(enemy.to_json(), owner_id)
        return enemy

    # =========================
    # SAVE
    # =========================
    def save(self, enemy: Enemy):
        data = enemy.to_json()
        self.repo.save(data, enemy.owner_id)

    # =========================
    # LOAD
    # =========================
    def load(self, enemy_id: str) -> Optional[Enemy]:
        data = self.repo.get_by_id(enemy_id)
        if data is None:
            return None

        return json_to_enemy(data)

    # =========================
    # DELETE
    # =========================
    def delete(self, enemy_id: str) -> bool:
        return self.repo.delete(enemy_id)

    # =========================
    # LIST BY OWNER
    # =========================
    def list_by_owner(self, owner_id: str) -> List[Enemy]:
        rows = self.repo.get_by_owner(owner_id)
        return [json_to_enemy(row) for row in rows]