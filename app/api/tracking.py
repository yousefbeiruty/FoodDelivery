import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, order_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(order_id, set()).add(websocket)

    async def disconnect(self, order_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(order_id, set())
            connections.discard(websocket)
            if not connections:
                self._connections.pop(order_id, None)

    async def publish(self, order_id: int, payload: dict) -> None:
        async with self._lock:
            connections = tuple(self._connections.get(order_id, set()))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                await self.disconnect(order_id, websocket)


manager = ConnectionManager()
