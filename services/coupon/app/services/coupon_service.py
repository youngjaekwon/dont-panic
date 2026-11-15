import base64
import secrets
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, Coupon
from app.repositories import coupon_gate
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.coupon_gate import CouponGate
from app.repositories.coupon_repository import (
    CouponRepository,
    DuplicateCodeError,
    SeqTakenError,
)
from app.services.exceptions import NotFound, NotStarted, SoldOut

_GATE_ERRORS = {
    coupon_gate.MISSING: NotFound,
    coupon_gate.NOT_STARTED: NotStarted,
    coupon_gate.SOLD_OUT: SoldOut,
}

CODE_RANDOM_BYTES = 10


def _new_code() -> str:
    return base64.b32encode(secrets.token_bytes(CODE_RANDOM_BYTES)).decode()


class CouponService:
    def __init__(
        self,
        session: AsyncSession,
        campaigns: CampaignRepository,
        coupons: CouponRepository,
        gate: CouponGate,
    ):
        self.session = session
        self.campaigns = campaigns
        self.coupons = coupons
        self.gate = gate

    async def create_campaign(self, name: str, total_quantity: int, starts_at: datetime) -> Campaign:
        if not name or total_quantity <= 0 or starts_at.tzinfo is None:
            raise ValueError("name is required, total_quantity must be positive, starts_at must include a timezone")
        async with self.session.begin():
            campaign = await self.campaigns.add(name, total_quantity, starts_at)
        await self.gate.seed(campaign.id, total_quantity, starts_at, 0)
        return campaign

    async def get_campaign(self, campaign_id: int) -> tuple[Campaign, int]:
        async with self.session.begin():
            campaign = await self.campaigns.get(campaign_id)
            if campaign is None:
                raise NotFound()
            return campaign, await self.coupons.count(campaign_id)

    async def list_coupons(self, campaign_id: int, after_seq: int, limit: int) -> list[Coupon]:
        async with self.session.begin():
            if await self.campaigns.get(campaign_id) is None:
                raise NotFound()
            return await self.coupons.list_after(campaign_id, after_seq, limit)

    async def issue(self, campaign_id: int) -> str:
        while True:
            seq = await self._admit(campaign_id)
            try:
                return await self._insert(campaign_id, seq)
            except SeqTakenError:
                continue
            except SoldOut:
                raise
            except BaseException:
                await self.gate.release(campaign_id, seq)
                raise

    async def _admit(self, campaign_id: int) -> int:
        res = await self.gate.admit(campaign_id)
        if res == coupon_gate.MISSING:
            await self._reseed(campaign_id)
            res = await self.gate.admit(campaign_id)
        if res < 0:
            raise _GATE_ERRORS[res]()
        return res

    async def _reseed(self, campaign_id: int) -> None:
        async with self.session.begin():
            campaign = await self.campaigns.get(campaign_id)
            if campaign is None:
                raise NotFound()
            max_seq = await self.coupons.max_seq(campaign_id)
        await self.gate.seed(campaign_id, campaign.total_quantity, campaign.starts_at, max_seq)

    async def _insert(self, campaign_id: int, seq: int) -> str:
        for _ in range(3):
            try:
                async with self.session.begin():
                    code = await self.coupons.insert_if_admissible(campaign_id, seq, _new_code())
            except DuplicateCodeError:
                continue
            if code:
                return code
            async with self.session.begin():
                started = await self.campaigns.has_started(campaign_id)
            raise SoldOut() if started else NotStarted()
        raise RuntimeError("coupon code collision")
