import uvicorn, random, time, sqlite3, json, uuid

from datetime import datetime, timedelta
from typing import Annotated, Dict

from fastapi import Depends, FastAPI, HTTPException, Response, Request, Cookie, Query, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import JWTError, jwt



from auth import * #ACCESS_TOKEN_EXPIRE_MINUTES, create_jwt_token, authenticate_user, get_current_active_user, get_user, reg_user
from models import * #UserRegister, Token, User

from dbApi import *

app = FastAPI()

class WebSocketManager:
    def __init__(self):
        self.websocket_connections: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.websocket_connections[websocket] = user_id

    async def disconnect(self, websocket: WebSocket):
        user_id = self.websocket_connections.get(websocket)
        if user_id:
            del self.websocket_connections[websocket]

    async def send_message(self, websocket: WebSocket, message: str):
        print(f"WS: {self.websocket_connections[websocket]} = {message}")
        await websocket.send_text(message)


    def get_connection(self, user_id):
        connection = [x for x, z in self.websocket_connections.items() if z == user_id]
        if connection: return connection[0]
        else: return False

manager = WebSocketManager()


########################################## ROUTES => PAGES #################################################
@app.get('/img/{filename}')
async def files_img(filename):
    return FileResponse(f'./pages/img/{filename}')


@app.get("/")
async def index_(): #Authorization: Annotated[str | None, Cookie()] = None
    return RedirectResponse(url="/login")

@app.get("/register")
async def getreg(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/register.html', encoding='utf-8').read())

@app.get("/login")
async def getreg(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/login.html', encoding='utf-8').read())

@app.get("/forgot")
async def getreg(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/forgot.html', encoding='utf-8').read())

@app.get("/reset")
async def getreg(token: str = Query(None, description="The reset token (recovery_token)"), Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    print(token)
    return HTMLResponse(open('pages/reset.html', encoding='utf-8').read())


@app.get("/chats")
async def chats(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)
    return HTMLResponse(open('pages/chats.html', encoding='utf-8').read())



########################################## ROUTES => CHATS #################################################
@app.get('/api/chats')
async def api_chats(Authorization: Annotated[str | None, Cookie()] = None, conversation_id: int = None):
    user = await get_current_user(Authorization)


    if conversation_id is None:
        conversations = db_getConversations(user.id)

        return {'status': True, 'conversations': conversations}

    else:
        messages = db_getMessages(user.id, conversation_id)

        return {'status': True, 'messages': messages}



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)

    await manager.connect(websocket, user.id)

    try:
        while True:
            data = await websocket.receive_text()
            print(f'data: {data}')

            chat_id = int(data.split(':')[0])
            type = data.split(':')[1]
            text = data.split(':')[2]
            print(f'message: {chat_id} | {type} | {text}')
            message = db_addMessage(user.id, chat_id, type, text)
            print(db_get_chat_users(chat_id))
            for x in db_get_chat_users(chat_id):
                message['is_me'] = x['user_id'] == user.id
                await manager.send_message(manager.get_connection(x['user_id']), json.dumps(message))
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(e)

@app.get('/test/{user_id}')
async def tests(user_id: int):
    connection = manager.get_connection(user_id)
    if connection: await manager.send_message(connection, 'hello my nigga')
    else: return False
    return 'hello my nigga'

@app.get('/test')
async def tests():
    return HTMLResponse(open('pages/index.html', encoding='utf-8').read())
############################################# AUTH #################################################
@app.get("/api/me")
async def get_me(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)

    return {'user_id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}    

@app.post("/api/forgot")
async def api_forgot(request_data: Forgot):
    user = get_user(request_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account with this username was not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    recovery_token_exiperes = timedelta(days=1)
    recovery_token = create_jwt_token(
        data={"user_id": user.id}, expires_delta=recovery_token_exiperes
    )

    return {"recovery_token": recovery_token}

@app.post("/api/reset")
async def api_forgot(request_data: Reset):
    #user = get_user(request_data.username)
    if False:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account with this username was not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif request_data.password != request_data.password_check:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passwords don't match",
            headers={"WWW-Authenticate": "Bearer"},
        )


    status = await reset_user(request_data.recovery_token, request_data.password)
    to_return = {'status': status['status']}

    if status['status']:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        print(status['username'])
        access_token = create_jwt_token(
            data={"sub": status['username']}, expires_delta=access_token_expires
        )

        to_return['access_token'] = access_token
        to_return['token_type'] = 'Berear'

    return to_return


@app.post("/api/auth", response_model=Token)
async def api_login(
    response: Response,
    request_data: UserLogin
):
    user = authenticate_user(request_data.username, request_data.password)
    if not user:
        raise HTTPException(
            status_code=202,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "Bearer"}


@app.post("/api/register", response_model=Token)
async def api_register(
    response: Response,
    request_data: UserRegister
):
    user = get_user(request_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username is already taken",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif len(request_data.username) < 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username length must be at least 4",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif len(request_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password length must be at least 6",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = reg_user(request_data)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "Bearer"}



############################################# OTHER #################################################


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    elif exc.detail == 'Already logged in':
        return RedirectResponse(url="/chats")

    return await http_exception_handler(request, exc)




if __name__ == '__main__':
    uvicorn.run(app, )