from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self._connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self._connections.pop(user_id, None)

    async def send_json(self, user_id: int, data: dict) -> None:
        ws = self._connections.get(user_id)
        if ws:
            await ws.send_json(data)

    def is_connected(self, user_id: int) -> bool:
        return user_id in self._connections


manager = ConnectionManager()
