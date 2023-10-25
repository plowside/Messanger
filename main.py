import uvicorn, time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from functions import *

class ConnectionManager:
	def __init__(self):
		self.active_connections = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_text(message)

	async def broadcast(self, message: str):
		for connection in self.active_connections:
			await connection.send_text(message)


app = FastAPI()
manager = ConnectionManager()











@app.get("/")
async def get():
	return HTMLResponse(open('pages/index.html', encoding='utf-8').read())

@app.get("/chats")
async def chats():
	return HTMLResponse(open('pages/chats.html', encoding='utf-8').read())

@app.get('/api/chats')
async def api_chats(chat_id: int = None):
	if chat_id is None:
		chats = [{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': "2023-10-25",},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': "1999-69-69",},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': "2001-11-11",},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': "2023-10-12",},'is_muted': True,},]
		return {'status': True, 'chats': chats}
	else:
		messages = [{'id': 1, 'user_id': 2, 'text': 'Привет!', 'ts': int(time.time())}]
		return {'status': True, 'messages': messages}





@app.get('/img/{filename}')
async def files_img(filename):
	return FileResponse(f'./pages/img/{filename}')


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
	await manager.connect(websocket)
	try:
		cur.execute('INSERT INTO users (id, ts) VALUES (?, ?)', [client_id, int(time.time())])
		con.commit()

		while True:
			data = await websocket.receive_text()
			await manager.send_personal_message(f"You wrote: {data}", websocket)
			await manager.broadcast(f"Client #{client_id}: {data}")

	except WebSocketDisconnect:
		manager.disconnect(websocket)
		await manager.broadcast(f"Client #{client_id} left the chat")



if __name__ == '__main__':
	uvicorn.run(app, host="192.168.0.13", port=8000)