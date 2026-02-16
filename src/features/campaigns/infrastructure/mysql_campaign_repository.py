from __future__ import annotations

from uuid import UUID
from src.shared.database.db_service import DatabaseService
from src.features.campaigns.ports.campaign_repository import CampaignRepository


class MySQLCampaignRepository(CampaignRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    # -----------------------------
    # Campaigns
    # -----------------------------

    def create(self, campaign_data: dict) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO campaigns (
                id, name, owner_id, world_id
            ) VALUES (%s, %s, %s, %s)
            """,
            (
                campaign_data["id"],
                campaign_data["name"],
                campaign_data["owner_id"],
                campaign_data.get("world_id"),
            )
        )
        self.db.commit()

    def get_by_id(self, campaign_id: UUID | str) -> dict | None:
        if isinstance(campaign_id, UUID):
            campaign_id = str(campaign_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM campaigns WHERE id = %s LIMIT 1",
            (campaign_id,)
        )
        return cur.fetchone()

    def get_by_owner(self, owner_id: UUID | str) -> list[dict]:
        if isinstance(owner_id, UUID):
            owner_id = str(owner_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM campaigns WHERE owner_id = %s",
            (owner_id,)
        )
        return cur.fetchall()

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
        return [row["user_id"] for row in cur.fetchall()]

    def get_campaigns_by_user(self, user_id: UUID | str) -> list[dict]:
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
        return cur.fetchall()

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
