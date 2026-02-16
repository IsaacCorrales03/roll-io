import uuid
from src.features.world.domain.token import Token
from src.features.world.ports.token_repository import TokenRepository


class TokenService:

    def __init__(self, repo: TokenRepository):
        self.repo = repo

    # -------------------------
    # CREATE
    # -------------------------
    def create(
        self,
        character_id: uuid.UUID,
        x: int,
        y: int,
        size: tuple[int, int] = (1, 1),
        texture_url: str | None = None,
        fallback_color: str = "#ff0000",
        owner_user_id: uuid.UUID | None = None,
        is_visible: bool = True,
        label: str = "",
    ) -> Token:

        token = Token(
            id=uuid.uuid4(),
            actor_id=character_id,
            x=x,
            y=y,
            size=size,
            texture_url=texture_url,
            fallback_color=fallback_color,
            owner_user_id=owner_user_id,
            is_visible=is_visible,
            label=label,
        )

        self.repo.create({
            "id": str(token.id),
            "character_id": str(character_id),
            "x": token.x,
            "y": token.y,
            "size_x": token.size[0],
            "size_y": token.size[1],
            "fallback_color": token.fallback_color,
            "owner_user_id": str(owner_user_id) if owner_user_id else None,
            "is_visible": token.is_visible,
            "label": token.label,
        })

        return token

    # -------------------------
    # GET BY CHARACTER
    # -------------------------
    def get_by_character(self, character_id: uuid.UUID):
        return self.repo.get_by_character(character_id)

    # -------------------------
    # MOVE
    # -------------------------
    def move(self, token_id: uuid.UUID, x: int, y: int):
        self.repo.update_position(token_id, x, y)

    # -------------------------
    # DELETE
    # -------------------------
    def delete(self, token_id: uuid.UUID):
        self.repo.delete(token_id)
