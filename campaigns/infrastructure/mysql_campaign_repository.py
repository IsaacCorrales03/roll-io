from uuid import UUID
from datetime import datetime
from services.db_service import DatabaseService
from campaigns.domain.campaign import Campaign
from campaigns.ports.campaign_repository import CampaignRepository


class MySQLCampaignRepository(CampaignRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    # -----------------------------
    # Campaigns
    # -----------------------------

    def create(self, campaign: Campaign) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO campaigns (
                id, name, owner_id, world, scenarios
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(campaign.id),
                campaign.name,
                str(campaign.owner_id),
                campaign.world,
                campaign.scenarios,
            )
        )
        self.db.commit()

    def get_by_id(self, campaign_id: UUID | str) -> Campaign | None:
        if isinstance(campaign_id, UUID):
            campaign_id = str(campaign_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM campaigns WHERE id = %s LIMIT 1",
            (campaign_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_campaign(row)  # type: ignore

    def get_by_owner(self, owner_id: UUID | str) -> list[Campaign]:
        if isinstance(owner_id, UUID):
            owner_id = str(owner_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM campaigns WHERE owner_id = %s",
            (owner_id,)
        )
        return [self._row_to_campaign(r) for r in cur.fetchall()]  # type: ignore

    # -----------------------------
    # Members
    # -----------------------------

    def add_member(self, campaign_id: UUID | str, user_id: UUID | str) -> None:
        if isinstance(campaign_id, UUID):
            campaign_id = str(campaign_id)
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        cur = self.db.cursor()
        cur.execute(
            """
            INSERT IGNORE INTO campaign_members (campaign_id, user_id)
            VALUES (%s, %s)
            """,
            (campaign_id, user_id)
        )
        self.db.commit()

    def get_members(self, campaign_id: UUID | str) -> list[str]:
        if isinstance(campaign_id, UUID):
            campaign_id = str(campaign_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT user_id FROM campaign_members WHERE campaign_id = %s",
            (campaign_id,)
        )
        return [row["user_id"] for row in cur.fetchall()]  # type: ignore
    def get_campaigns_by_user(self, user_id: UUID | str) -> list[Campaign]:
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT c.* FROM campaigns c
            JOIN campaign_members m ON c.id = m.campaign_id
            WHERE m.user_id = %s
            """,
            (user_id,)
        )
        return [self._row_to_campaign(r) for r in cur.fetchall()]  # type: ignore
    def is_member(self, campaign_id: UUID | str, user_id: UUID | str) -> bool:
        if isinstance(campaign_id, UUID):
            campaign_id = str(campaign_id)
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        cur = self.db.cursor()
        cur.execute(
            """
            SELECT 1 FROM campaign_members
            WHERE campaign_id = %s AND user_id = %s
            LIMIT 1
            """,
            (campaign_id, user_id)
        )
        return cur.fetchone() is not None

    
    # -----------------------------
    # Mapper
    # -----------------------------

    def _row_to_campaign(self, row: dict) -> Campaign:
        return Campaign(
            id=UUID(row["id"]),
            name=row["name"],
            owner_id=UUID(row["owner_id"]),
            world=row["world"],
            scenarios=row["scenarios"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
    