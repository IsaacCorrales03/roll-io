from uuid import UUID
from typing import Tuple


class Token:

    def __init__(
        self,
        id: UUID,
        actor_id: UUID,
        x: int,
        y: int,
        size: Tuple[int, int] = (1, 1),

        texture_url: str | None = None,
        fallback_color: str = "#ff0000",

        owner_user_id: UUID | None = None,
        is_visible: bool = True,
        label: str = "",
    ):
        self.id = id
        self.actor_id = actor_id
        self.x = x
        self.y = y
        self.size = size

        self.fallback_color = fallback_color

        self.owner_user_id = owner_user_id
        self.is_visible = is_visible
        self.label = label
    def to_dict(self):
        return {
            "id": str(self.id),
            "actor_id": str(self.actor_id),
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "fallback_color": self.fallback_color,
            "owner_user_id": str(self.owner_user_id) if self.owner_user_id else None,
            "is_visible": self.is_visible,
            "label": self.label,
        }
