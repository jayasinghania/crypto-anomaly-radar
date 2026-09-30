"""
Phase 5 - WebSocket connection manager + Redis subscriber.

One background task per server process subscribes to Redis pub/sub and
fans each message out to every currently-connected WebSocket client.
Ingestion and analytics never need to know how many browser tabs are
open - they just publish, and this is the only piece that cares who's
listening.
"""

from __future__ import annotations

import logging

from fastapi import WebSocket

from app.realtime.publisher import ANOMALIES_CHANNEL, METRICS_CHANNEL, TICKS_CHANNEL, get_redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        # Iterate over a copy - a client can disconnect mid-broadcast.
        for connection in list(self._connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


async def redis_listener() -> None:
    """Subscribe to Redis once per server process, forward every message to all connected clients."""
    client = get_redis_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(TICKS_CHANNEL, METRICS_CHANNEL, ANOMALIES_CHANNEL)
    logger.info(
        "Subscribed to Redis channels: %s, %s, %s",
        TICKS_CHANNEL, METRICS_CHANNEL, ANOMALIES_CHANNEL,
    )

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        await manager.broadcast(message["data"])
