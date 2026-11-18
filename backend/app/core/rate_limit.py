from redis.asyncio import Redis


TAKE_SLOT = """
if redis.call('SET', KEYS[1], 1, 'EX', ARGV[2], 'NX') then
    return 0
end
if tonumber(redis.call('GET', KEYS[1])) < tonumber(ARGV[1]) then
    redis.call('INCR', KEYS[1])
    return 0
end
return math.max(1, redis.call('TTL', KEYS[1]))
"""


class RateLimiter:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def retry_after(self, key: str, limit: int, window_seconds: int) -> int:
        return await self.redis.eval(TAKE_SLOT, 1, f"rag:rate:{key}", limit, window_seconds)
