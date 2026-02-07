import uuid
from typing import Optional, List

from campaigns.domain.campaign import Campaign
from campaigns.infrastructure.mysql_campaign_repository import CampaignRepository


class CampaignService:
    def __init__(self, repo: CampaignRepository):
        self.repo = repo

    def create(self, owner_id: uuid.UUID, name: str) -> Campaign:
        campaign = Campaign(
            id=uuid.uuid4(),
            name=name,
            owner_id=owner_id,
            world="",
            scenarios=""
        )

        # crear campaña
        self.repo.create(campaign)

        # añadir owner como miembro (rol DM implícito si lo manejas)
        self.repo.add_member(campaign.id, owner_id)

        return campaign

    def load(self, campaign_id: str) -> Optional[Campaign]:
        data = self.repo.get_by_id(campaign_id)
        if data is None:
            return None
        return data

    def get_by_user(self, user_id: uuid.UUID) -> List[Campaign]:
        rows = self.repo.get_campaigns_by_user(user_id)
        return rows

    def join(self, campaign_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.repo.add_member(campaign_id, user_id)
