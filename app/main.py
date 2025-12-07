from fastapi import FastAPI
from app.api.ws import router as ws_router, pubsub_listener
import asyncio

app = FastAPI()
app.include_router(ws_router)


@app.on_event("startup")
async def start_pubsub():
    asyncio.create_task(pubsub_listener())
