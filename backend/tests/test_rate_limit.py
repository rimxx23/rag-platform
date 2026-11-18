import asyncio
import os
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.core.rate_limit import RateLimiter


@pytest.mark.skipif(not os.getenv("TEST_REDIS_URL"), reason="TEST_REDIS_URL is not set")
def test_redis_limit_is_atomic_and_resets():
    async def run():
        key = uuid4().hex
        async with Redis.from_url(os.environ["TEST_REDIS_URL"]) as redis:
            limiter = RateLimiter(redis)
            results = await asyncio.gather(
                *(limiter.retry_after(key, limit=4, window_seconds=8) for _ in range(12))
            )
            assert results.count(0) == 4
            assert all(1 <= ttl <= 8 for ttl in results if ttl)
            assert await limiter.retry_after(f"{key}:other", 4, 8) == 0

            short_key = f"{key}:expiry"
            assert await limiter.retry_after(short_key, 1, 1) == 0
            assert await limiter.retry_after(short_key, 1, 1) == 1
            await asyncio.sleep(1.05)
            assert await limiter.retry_after(short_key, 1, 1) == 0

    asyncio.run(run())
