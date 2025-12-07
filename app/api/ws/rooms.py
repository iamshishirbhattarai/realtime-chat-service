from typing import Dict, Set
from fastapi import WebSocket

from app.core import redis_client


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    def create_room(self, room: str):
        if room not in self.rooms:
            self.rooms[room] = set()

    async def join_room(self, room: str, websocket: WebSocket):
        self.create_room(room)
        self.rooms[room].add(websocket)
        await websocket.accept()

    async def leave_room(self, room: str, websocket: WebSocket):
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)

    async def broadcast(self, room: str, message: str):
        if room not in self.rooms:
            return
        dead_connections = set()
        for connection in self.rooms[room]:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.add(connection)
        for connection in dead_connections:
            self.rooms[room].remove(connection)

    async def publish(self, room: str, message: str):
        print("Publishing to Redis:", room, message)
        subscribers = await redis_client.publish(f"room:{room}", message)
        print("Redis subscribers count:", subscribers)

    async def disconnect(self, websocket: WebSocket):
        for room in self.rooms.values():
            if websocket in room:
                room.remove(websocket)
