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


PRESENCE_TTL = 60  # seconds


async def set_user_online(user_id: str) -> None:
    await redis_client.setex(f"presence:{user_id}", PRESENCE_TTL, "1")


async def refresh_user_presence(user_id: str) -> None:
    await redis_client.expire(f"presence:{user_id}", PRESENCE_TTL)


async def set_user_offline(user_id: str) -> None:
    await redis_client.delete(f"presence:{user_id}")


async def is_user_online(user_id: str) -> bool:
    return await redis_client.exists(f"presence:{user_id}") > 0
