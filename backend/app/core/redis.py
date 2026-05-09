import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(
    settings.redis_url, decode_responses=True, max_connections=100
)


def get_pubsub():
    return redis_client.pubsub()


async def blacklist_token(token: str, ttl: int) -> None:
    await redis_client.setex(f"blacklist:{token}", ttl, "true")


async def is_token_blacklisted(token: str) -> bool:
    return await redis_client.exists(f"blacklist:{token}") > 0
