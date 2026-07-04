"""
NEXUS — Redis connection management.
Used for: caching, Celery result backend interop, pub/sub for
real-time job progress pushed out over WebSocket.
"""
import json
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as redis

from core.config import settings

_pool: Optional[redis.ConnectionPool] = None


def get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, decode_responses=True, max_connections=50
        )
    return _pool


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=get_pool())


class RedisClient:
    """Thin async wrapper with helpers used throughout the app."""

    def __init__(self) -> None:
        self.client = get_redis()

    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        await self.client.set(key, json.dumps(value), ex=ex)

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self.client.get(key)
        return json.loads(raw) if raw else None

    async def publish_json(self, channel: str, payload: Any) -> None:
        await self.client.publish(channel, json.dumps(payload))

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self) -> None:
        await self.client.aclose()


redis_client = RedisClient()
