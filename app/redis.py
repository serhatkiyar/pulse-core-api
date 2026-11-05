from collections.abc import AsyncGenerator

from redis import asyncio as redis

from .config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True, max_connections=10
)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
