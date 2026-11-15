from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign


class CampaignRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, name: str, total_quantity: int, starts_at: datetime) -> Campaign:
        campaign = Campaign(name=name, total_quantity=total_quantity, starts_at=starts_at)
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def get(self, campaign_id: int) -> Campaign | None:
        return await self.session.get(Campaign, campaign_id)

    async def has_started(self, campaign_id: int) -> bool:
        return bool(
            await self.session.scalar(select(Campaign.starts_at <= func.now()).where(Campaign.id == campaign_id))
        )
