from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID
import datetime as _dt


@dataclass
class Campaign:
    id: UUID
    name: str
    owner_id: UUID
    users: list[UUID] = field(default_factory=list)
    world_id: UUID | None = None
    created_at: _dt.datetime | None = None
    updated_at: _dt.datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Campaign:
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            owner_id=UUID(data["owner_id"]),
            users=[UUID(u) for u in data.get("users", [])],
            world_id=UUID(data["world_id"]) if data.get("world_id") else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "owner_id": str(self.owner_id),
            "users": [str(u) for u in self.users],
            "world_id": str(self.world_id) if self.world_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
