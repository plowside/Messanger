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

    async def on_disconnect(self, websocket: WebSocket):
        try:
            await websocket.close()
        except: pass

        await self.disconnect(websocket)


    async def send_message(self, websocket: WebSocket, message):
        if type(message) == str:
            await websocket.send_text(message)
        elif type(message) == dict:
            await websocket.send_json(message)


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

    return HTMLResponse(open('pages/reset.html', encoding='utf-8').read())


@app.get("/dialogs")
async def dialogs(Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)
    return HTMLResponse(open('pages/dialogs.html', encoding='utf-8').read())



########################################## ROUTES => dialogs #################################################
@app.get('/api/dialogs')
async def api_dialogs(Authorization: Annotated[str | None, Cookie()] = None, dialog_id: int = None):
    user = await get_current_user(Authorization)


    if dialog_id is None:
        dialogs = db_get_dialogs(user_id=user.id)

        return {'status': True, 'dialogs': dialogs}

    else:
        messages = db_get_messages(dialog_id=dialog_id)

        return {'status': True, 'messages': messages}


@app.get("/api/find")
async def api_find(q: str = Query(None, description="Search query"), Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)

    results = db_find_dialogs(user.id, q)
    return {'status': True, 'results': results}


@app.get("/api/dialog")
async def api_find(id: int = Query(None, description="User id"), Authorization: Annotated[str | None, Cookie()] = None):
    user = await get_current_user(Authorization)
    user_target = get_user(user_id=id)

    dialog_id = db_create_dialog(user.id, user_target.id, dialog_name = None)#user_target.username if (user_target.first_name is None or user_target.last_name is None) else f'{user_target.first_name if user_target.last_name is None else user_target.last_name}{" " + user_target.last_name if user_target.last_name is None else ""}'
    if not dialog_id:
        return {'status': False}

    message = {'update':'new_dialog', 'data': {'dialog_id': dialog_id}}
    try: await manager.send_message(manager.get_connection(user_target.id), message)
    except Exception as e: print(f'errro: {e}')

    dialogs = db_get_dialogs(user_id=user.id)
    return {'status': True, 'dialogs': dialogs}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, Authorization: Annotated[str | None, Cookie()] = None):
    try: user = await get_current_user(Authorization)
    except Exception as e:
        await manager.on_disconnect(websocket)
        raise e

    await manager.connect(websocket, user.id)
    while True:
        try:
            data = await websocket.receive_json()
            if data == '': continue
            elif 'ping' in data:
                await manager.send_message(websocket, 'pong')
                continue


            print(f'data: {data}')
            dialog_id = data.get('dialog_id')
            message_type = data.get('message_type')
            message_text = data.get('message_text')
            if message_text == '': continue
            message_id = db_create_message(dialog_id=dialog_id, sender_id=user.id, message_type=message_type, message_text=message_text, send_time=int(time.time()))
            message = {'update': 'new_message', 'data': db_get_messages(dialog_id, message_id)}

            for x in db_get_dialog_users(dialog_id):
                try: await manager.send_message(manager.get_connection(x['user_id']), message)
                except :pass

        except WebSocketDisconnect:
            return await manager.disconnect(websocket)
        except ValueError:
            continue
        except Exception as e:
            print(f"error on Websocket: {e}")


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

    return {'user_id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'registration_date': user.registration_date}    



@app.post("/api/forgot")
async def api_forgot(request_data: Forgot):
    user = get_user(username=request_data.username)
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
    #user = get_user(username=request_data.username)
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
        access_token = create_jwt_token(
            data={"sub": status['user'].username}, expires_delta=access_token_expires
        )

        to_return['access_token'] = access_token
        to_return['token_type'] = 'Berear'
        to_return['live_time'] = ACCESS_TOKEN_EXPIRE_MINUTES

    return to_return


@app.post("/api/auth")
async def api_login(response: Response, request_data: UserLogin):
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

    return {"access_token": access_token, "token_type": "Bearer", "live_time": ACCESS_TOKEN_EXPIRE_MINUTES}


@app.post("/api/register")
async def api_register(response: Response, request_data: UserRegister):
    user = get_user(username=request_data.username)
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

    return {"access_token": access_token, "token_type": "Bearer", "live_time": ACCESS_TOKEN_EXPIRE_MINUTES}



############################################# OTHER #################################################


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    elif exc.detail == 'Already logged in':
        return RedirectResponse(url="/dialogs")

    return await http_exception_handler(request, exc)




if __name__ == '__main__':
    uvicorn.run(app)