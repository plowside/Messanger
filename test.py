import uvicorn, sqlite3, time, json, random
import MySQLdb

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, Request, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt

from functions import *

con = sqlite3.connect('db.db')
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    hashed_password TEXT,
    registration_date INTEGER,
    avatar TEXT,
    last_online INTEGER,
    access_type INTEGER DEFAULT(1)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    converstaion_name TEXT,
    converstaion_avatar TEXT,
    converstaion_type TEXT,
    show_type INTEGER DEFAULT (1)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    message_id INTEGER,
    message_type TEXT,
    message_data TEXT,
    from_id INTEGER
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_settings(
    user_id INTEGER,
    conversation_id INTEGER,
    is_muted BOOL DEFAULT (False)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_updates(
    user_id INTEGER,
    conversation_id INTEGER,
    update_type TEXT,
    update_data TEXT
    )''')
con.commit()




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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserInDB(User):
    hashed_password: str

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None



def fake_hash_password(password: str):
    return "fakehashed" + password

def fake_decode_token(token):
    return User(username=token + "fakedecoded", email="john@example.com", full_name="John Doe")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user


@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user






def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(cur.execute('SELECT '), token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user













@app.post('/api/auth')
async def passf():
    pass


@app.get("/")
async def get():
    return HTMLResponse(open('pages/index.html', encoding='utf-8').read())



@app.get("/chats")
async def chats():
    return HTMLResponse(open('pages/chats.html', encoding='utf-8').read())



@app.get('/api/chats')
async def api_chats(chat_id: int = None):
    if chat_id is None:
        chats = [{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},{'id': 1,'name': "kolenocka",'last_message': {'text': "го тарков",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 2,'name': "Буль буль | Толя",'last_message': {'text': "Ок",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 3,'name': "SKIFY",'last_message': {'text': "*обзывает меня",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': False,},{'id': 4,'name': "Хохол негройдной рассы (раян)",'last_message': {'text': "пошли в рор",'date': int(time.time()-random.randint(1, 9999999)),},'is_muted': True,},]
        return {'status': True, 'chats': chats}
    else:
        messages = [{'message_id': 1, 'user_id': 2, 'is_me': True, 'message_type': 'message', 'text': 'Привет!', 'ts': int(time.time())}, {'message_id': 2, 'user_id': 2, 'message_type': 'local_update', 'text': 'Собеседник сделал скриншот', 'ts': int(time.time())}]
        return {'status': True, 'messages': messages}





@app.get('/img/{filename}')
async def files_img(filename):
    return FileResponse(f'./pages/img/{filename}')



@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")



if __name__ == '__main__':
    uvicorn.run(app)