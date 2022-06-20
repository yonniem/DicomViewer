from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        ws = self.active_connections[client_id]
        await ws.send_text(message)

    async def broadcast(self, message: str):
        keys = list(self.active_connections)
        print(keys)

    async def send_client_id(self, client_id):
        wrapper = {
            "wslink": "1.0",
            "id": "system:c0:0",
            "result": {
                "clientID": client_id
            }
        }
        ws = self.active_connections[client_id]
        await ws.send_json(wrapper)
