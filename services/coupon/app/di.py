from collections.abc import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from redis.asyncio import BlockingConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.coupon_gate import CouponGate
from app.repositories.coupon_repository import CouponRepository
from app.services.coupon_service import CouponService


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return Settings()  # pyright: ignore[reportCallIssue]

    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(settings.database_url, pool_size=settings.pg_pool_size, max_overflow=0)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.APP)
    async def redis(self, settings: Settings) -> AsyncIterator[Redis]:
        pool = BlockingConnectionPool.from_url(settings.redis_url, max_connections=settings.redis_pool_size, timeout=5)
        redis = Redis.from_pool(pool)
        yield redis
        await redis.aclose()

    gate = provide(CouponGate, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def session(self, session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
        session = session_maker()
        try:
            yield session
        finally:
            if session.in_transaction() or session.identity_map:
                await session.close()

    campaigns = provide(CampaignRepository, scope=Scope.REQUEST)
    coupons = provide(CouponRepository, scope=Scope.REQUEST)
    service = provide(CouponService, scope=Scope.REQUEST)


def create_container():
    return make_async_container(AppProvider())
