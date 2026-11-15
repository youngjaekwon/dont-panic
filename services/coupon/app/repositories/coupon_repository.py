from sqlalchemy import bindparam, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, Coupon
from app.models.coupon import SEQ_UNIQUE

_ISSUE = (
    insert(Coupon)
    .from_select(
        ["campaign_id", "seq", "code"],
        select(Campaign.id, bindparam("seq"), bindparam("code")).where(
            Campaign.id == bindparam("campaign_id"),
            Campaign.total_quantity >= bindparam("seq"),
            Campaign.starts_at <= func.now(),
        ),
    )
    .returning(Coupon.code)
)


class SeqTakenError(Exception):
    pass


class DuplicateCodeError(Exception):
    pass


class CouponRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_if_admissible(self, campaign_id: int, seq: int, code: str) -> str | None:
        conn = await self.session.connection(execution_options={"isolation_level": "AUTOCOMMIT"})
        try:
            return await conn.scalar(_ISSUE, {"campaign_id": campaign_id, "seq": seq, "code": code})
        except IntegrityError as e:
            if getattr(e.orig.__cause__, "constraint_name", None) == SEQ_UNIQUE:
                raise SeqTakenError() from e
            raise DuplicateCodeError() from e

    async def count(self, campaign_id: int) -> int:
        return (await self.session.execute(select(func.count()).where(Coupon.campaign_id == campaign_id))).scalar_one()

    async def list_after(self, campaign_id: int, after_seq: int, limit: int) -> list[Coupon]:
        stmt = (
            select(Coupon)
            .where(Coupon.campaign_id == campaign_id, Coupon.seq > after_seq)
            .order_by(Coupon.seq)
            .limit(limit)
        )
        return list(await self.session.scalars(stmt))

    async def max_seq(self, campaign_id: int) -> int:
        return await self.session.scalar(
            select(func.coalesce(func.max(Coupon.seq), 0)).where(Coupon.campaign_id == campaign_id)
        )
