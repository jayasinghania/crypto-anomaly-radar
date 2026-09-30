from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.broadcaster import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client - this just keeps
            # the connection open and lets us detect a disconnect.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
