from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from typing import List

@dataclass
class Campaign:
    id: UUID
    name: str
    owner_id: UUID
    users: List[UUID] = field(default_factory=list)
    world: str = ""
    scenarios: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Campaign":
        return cls(
            id=UUID(data.get("id")) if data.get("id") else UUID(int=0),
            name=data.get("name", ""),
            owner_id=UUID(data.get("owner_id")) if data.get("owner_id") else UUID(int=0),
            users=[UUID(u) if isinstance(u, str) else u for u in data.get("users", [])],
            world=data.get("world", ""),
            scenarios=data.get("scenarios", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    @classmethod
    def to_dict(cls, campaign: "Campaign") -> dict:
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "owner_id": str(campaign.owner_id),
            "users": [str(u) for u in campaign.users],
            "world": campaign.world,
            "scenarios": campaign.scenarios,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        }