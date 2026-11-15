from datetime import datetime

from redis.asyncio import Redis

MISSING, NOT_STARTED, SOLD_OUT = -1, -2, -3

_ADMIT = """
local h = redis.call('HMGET', KEYS[1], 'total', 'starts_at_ms', 'admitted')
if not h[1] then return -1 end
local t = redis.call('TIME')
if tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000) < tonumber(h[2]) then return -2 end
local freed = redis.call('LPOP', KEYS[2])
if freed then return tonumber(freed) end
if tonumber(h[3]) >= tonumber(h[1]) then return -3 end
return redis.call('HINCRBY', KEYS[1], 'admitted', 1)
"""

_SEED = """
if redis.call('EXISTS', KEYS[1]) == 0 then
    redis.call('HSET', KEYS[1], 'total', ARGV[1], 'starts_at_ms', ARGV[2], 'admitted', ARGV[3])
end
"""


class CouponGate:
    def __init__(self, redis: Redis):
        self.redis = redis
        self._admit = redis.register_script(_ADMIT)
        self._seed = redis.register_script(_SEED)

    @staticmethod
    def keys(campaign_id: int) -> list[str]:
        return [f"campaign:{{{campaign_id}}}", f"campaign:{{{campaign_id}}}:free"]

    async def admit(self, campaign_id: int) -> int:
        return await self._admit(keys=self.keys(campaign_id))

    async def release(self, campaign_id: int, seq: int) -> None:
        await self.redis.lpush(self.keys(campaign_id)[1], seq)

    async def seed(self, campaign_id: int, total_quantity: int, starts_at: datetime, admitted: int) -> None:
        await self._seed(
            keys=self.keys(campaign_id), args=[total_quantity, int(starts_at.timestamp() * 1000), admitted]
        )
