from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging
import json
import os
import asyncio
import redis.asyncio as redis

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"]
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class ConnectionManager:
    def __init__(self):
        # Maps account_id to a list of active local WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Keep track of Redis pubsub listener tasks per account
        self.listeners: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, account_id: str):
        await websocket.accept()
        if account_id not in self.active_connections:
            self.active_connections[account_id] = []
            # Start a Redis pubsub listener for this account
            self.listeners[account_id] = asyncio.create_task(self._listen_to_redis(account_id))
        self.active_connections[account_id].append(websocket)
        logger.info(f"WebSocket connected for account {account_id}")

    def disconnect(self, websocket: WebSocket, account_id: str):
        if account_id in self.active_connections:
            if websocket in self.active_connections[account_id]:
                self.active_connections[account_id].remove(websocket)
            if not self.active_connections[account_id]:
                del self.active_connections[account_id]
                # Stop the Redis listener if no local clients remain
                if account_id in self.listeners:
                    self.listeners[account_id].cancel()
                    del self.listeners[account_id]
        logger.info(f"WebSocket disconnected for account {account_id}")

    async def _listen_to_redis(self, account_id: str):
        pubsub = redis_client.pubsub()
        channel_name = f"account:{account_id}"
        await pubsub.subscribe(channel_name)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # Broadcast to all local connections for this account
                    if account_id in self.active_connections:
                        for connection in self.active_connections[account_id]:
                            try:
                                await connection.send_text(data) # We published JSON string, so send_text
                            except Exception as e:
                                logger.error(f"Error sending message to account {account_id}: {e}")
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    async def broadcast_to_account(self, account_id: str, message: dict):
        """
        Sends a JSON message via Redis Pub/Sub to reach all connected clients
        across all server instances.
        """
        channel_name = f"account:{account_id}"
        await redis_client.publish(channel_name, json.dumps(message))

manager = ConnectionManager()

@router.websocket("/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    await manager.connect(websocket, account_id)
    try:
        while True:
            # We don't necessarily expect messages from the client in this design,
            # but we need to keep the connection alive and handle disconnects.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, account_id)
