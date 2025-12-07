import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.ws.rooms import RoomManager
from app.core.redis import get_pubsub

room_manager = RoomManager()
router = APIRouter()


@router.websocket("/ws/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    await room_manager.join_room(room_name, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await room_manager.publish(room_name, data)
    except WebSocketDisconnect:
        await room_manager.leave_room(room_name, websocket)


async def pubsub_listener():
    pubsub = get_pubsub()
    await pubsub.psubscribe("room:*")
    print("PubSub listener started")

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            print("Redis message:", message)  # debug log
            channel = message["channel"]
            data = message["data"]
            room = channel.replace("room:", "")
            await room_manager.broadcast(room, data)

        await asyncio.sleep(0.01)
