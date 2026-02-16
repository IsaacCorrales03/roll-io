from __future__ import annotations

import uuid
from src.features.campaigns.infrastructure.mysql_campaign_repository import CampaignRepository
from src.features.campaigns.domain.campaign import Campaign

def load(self, campaign_id: str):
    data = self.repo.get_by_id(campaign_id)
    if not data:
        return None
    return Campaign.from_dict(data)

class CampaignService:
    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        world_id: uuid.UUID,
    ):
        # import lazy del dominio
        from src.features.campaigns.domain.campaign import Campaign

        campaign = Campaign(
            id=uuid.uuid4(),
            name=name,
            owner_id=owner_id,
            world_id=world_id,
        )

        self.repo.create(campaign.to_dict())
        self.repo.add_member(campaign.id, owner_id)

        return campaign

    def load(self, campaign_id: str):
        return self.repo.get_by_id(campaign_id)

    def get_by_user(self, user_id: uuid.UUID):
        return self.repo.get_campaigns_by_user(user_id)

    def join(self, campaign_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.repo.add_member(campaign_id, user_id)
