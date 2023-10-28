import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict

app = FastAPI()

class WebSocketManager:
    def __init__(self):
        self.websocket_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.websocket_connections[websocket] = username

    async def disconnect(self, websocket: WebSocket):
        username = self.websocket_connections.get(websocket)
        if username:
            print(self.websocket_connections[websocket])
            del self.websocket_connections[websocket]


    async def send_message(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)

manager = WebSocketManager()

@app.get('/')
async def index_():
    return HTMLResponse(open('pages/index.html', encoding='utf-8').read())

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            message = f"{username}: {data}"
            for ws, user in manager.websocket_connections.items():
                await manager.send_message(ws, message)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

if __name__ == '__main__':
    uvicorn.run(app)