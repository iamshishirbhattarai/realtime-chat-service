import asyncio
from logging import getLogger

from fastapi import FastAPI

from app.api.ws.websocket import pubsub_listener
from app.core.redis import redis_client

logger = getLogger(__name__)


async def init_pubsub(app: FastAPI) -> None:
    """
    Start the Redis PubSub listener and store the task on app.state.
    """
    logger.info("Initializing PubSub listener task")
    task = asyncio.create_task(pubsub_listener())
    app.state.pubsub_task = task


async def shutdown_pubsub(app: FastAPI) -> None:
    """
    Stop the Redis PubSub listener and close Redis client.
    """
    task = getattr(app.state, "pubsub_task", None)

    if task is not None:
        logger.info("Stopping PubSub listener task")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    try:
        await redis_client.close()
        print("Redis client closed")
    except Exception as e:
        logger.error("Error while closing Redis client: %s", e)
