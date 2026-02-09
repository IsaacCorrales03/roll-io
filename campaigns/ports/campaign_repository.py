from abc import ABC, abstractmethod
from uuid import UUID
from ..domain.campaign import Campaign

class CampaignRepository(ABC):

    @abstractmethod
    def create(self, campaign_data: dict) -> None: ...

    @abstractmethod
    def get_by_id(self, campaign_id: UUID | str) -> dict | None: ...

    @abstractmethod
    def get_by_owner(self, owner_id: UUID | str) -> list[dict]: ...

    @abstractmethod
    def add_member(self, campaign_id: UUID | str, user_id: UUID | str) -> None: ...

    @abstractmethod
    def get_members(self, campaign_id: UUID | str) -> list[str]: ...

    @abstractmethod
    def get_campaigns_by_user(self, user_id: UUID | str) -> list[dict]: ...