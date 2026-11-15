import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.repositories.coupon_gate import CouponGate
from app.services.coupon_service import CouponService
from app.services.exceptions import NotFound, NotStarted, SoldOut


@pytest.fixture
async def call(container):
    async def run(method: str, *args):
        async with container() as request:
            service = await request.get(CouponService)
            return await getattr(service, method)(*args)

    return run


@pytest.fixture
async def redis(container) -> Redis:
    return await container.get(Redis)


@pytest.fixture
async def sql(container):
    engine = await container.get(AsyncEngine)

    async def run(query: str, **params):
        async with engine.begin() as conn:
            result = await conn.execute(text(query), params)
            return result.all() if result.returns_rows else None

    return run


@pytest.fixture
def campaign(call):
    async def make(total: int, start_in: float = -1.0) -> int:
        c = await call("create_campaign", "t", total, datetime.now(UTC) + timedelta(seconds=start_in))
        return c.id

    return make


@pytest.fixture
def burst(call):
    async def run(cid: int, n: int):
        res = await asyncio.gather(*(call("issue", cid) for _ in range(n)), return_exceptions=True)
        return [x for x in res if isinstance(x, str)], [x for x in res if not isinstance(x, str)]

    return run


@pytest.fixture
def pg_codes(sql):
    async def run(cid: int) -> list[str]:
        return [r.code for r in await sql("SELECT code FROM coupons WHERE campaign_id = :cid", cid=cid)]

    return run


async def test_no_overissue_unique_codes(campaign, burst, pg_codes):
    cid = await campaign(100)
    ok, errs = await burst(cid, 500)
    assert len(ok) == 100 == len(set(ok))
    assert all(isinstance(e, SoldOut) for e in errs), {type(e) for e in errs}
    assert sorted(await pg_codes(cid)) == sorted(ok)


async def test_not_started(campaign, burst, pg_codes):
    cid = await campaign(100, start_in=3600)
    ok, errs = await burst(cid, 200)
    assert ok == [] and all(isinstance(e, NotStarted) for e in errs)
    assert await pg_codes(cid) == []


async def test_nothing_issued_before_start_time(campaign, burst, sql):
    cid = await campaign(30, start_in=0.5)
    for _ in range(20):
        await burst(cid, 20)
        await asyncio.sleep(0.05)
    [row] = await sql(
        "SELECT count(*) AS n, min(cp.issued_at) >= c.starts_at AS ok FROM campaigns c "
        "JOIN coupons cp ON cp.campaign_id = c.id WHERE c.id = :cid GROUP BY c.starts_at",
        cid=cid,
    )
    assert row.n == 30 and row.ok


async def test_redis_counter_regressed(campaign, burst, pg_codes, redis):
    cid = await campaign(100)
    ok1, _ = await burst(cid, 60)
    await redis.hset(CouponGate.keys(cid)[0], "admitted", 0)
    ok2, _ = await burst(cid, 300)
    assert len(ok1) + len(ok2) == 100 == len(await pg_codes(cid))
    assert int(await redis.hget(CouponGate.keys(cid)[0], "admitted")) >= 100


async def test_redis_key_lost_reseeds_from_pg(campaign, burst, pg_codes, redis):
    cid = await campaign(100)
    ok1, _ = await burst(cid, 30)
    await redis.delete(*CouponGate.keys(cid))
    ok2, _ = await burst(cid, 300)
    assert len(ok1) == 30 and len(ok2) == 70
    assert len(await pg_codes(cid)) == 100


async def test_failed_seq_is_reused(campaign, call, sql):
    cid = await campaign(1)
    await sql("UPDATE campaigns SET starts_at = now() + interval '1 hour' WHERE id = :cid", cid=cid)
    with pytest.raises(NotStarted):
        await call("issue", cid)
    await sql("UPDATE campaigns SET starts_at = now() - interval '1 second' WHERE id = :cid", cid=cid)
    assert await call("issue", cid)
    with pytest.raises(SoldOut):
        await call("issue", cid)


async def test_not_found(call):
    with pytest.raises(NotFound):
        await call("issue", 2**62)
    with pytest.raises(NotFound):
        await call("get_campaign", 2**62)
