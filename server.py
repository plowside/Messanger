import uvicorn, random, time, sqlite3, json

from datetime import datetime, timedelta
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, Response, Request, Cookie, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import JWTError, jwt



from auth import *#ACCESS_TOKEN_EXPIRE_MINUTES, create_jwt_token, authenticate_user, get_current_active_user, get_user, reg_user
from models import *#UserRegister, Token, User

from dbApi import *

app = FastAPI()


########################################## ROUTES => PAGES #################################################
@app.get('/img/{filename}')
async def files_img(filename):
    return FileResponse(f'./pages/img/{filename}')


@app.get("/")
async def index_(): #Authorization: Annotated[Union[str, None], Cookie()] = None
    return RedirectResponse(url="/login")

@app.get("/register")
async def getreg(Authorization: Annotated[Union[str , None], Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/register.html', encoding='utf-8').read())

@app.get("/login")
async def getreg(Authorization: Annotated[Union[str , None], Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/login.html', encoding='utf-8').read())

@app.get("/forgot")
async def getreg(Authorization: Annotated[Union[str , None], Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/forgot.html', encoding='utf-8').read())

@app.get("/reset")
async def getreg(Authorization: Annotated[Union[str , None], Cookie()] = None):
    user = await get_current_user_None(Authorization)
    if user:
        raise HTTPException(
            status_code=200,
            detail="Already logged in",
            headers={},
        )
    return HTMLResponse(open('pages/reset.html', encoding='utf-8').read())


@app.get("/chats")
async def chats(Authorization: Annotated[Union[str , None], Cookie()] = None):
    user = await get_current_user(Authorization)
    return HTMLResponse(open('pages/chats.html', encoding='utf-8').read())



########################################## ROUTES => CHATS #################################################
@app.get('/api/chats')
async def api_chats(Authorization: Annotated[Union[str , None], Cookie()] = None, conversation_id: int = None):
    user = await get_current_user(Authorization)
    _db = SQLiteDatabase()
    cur, con = _db._get_connection()

    if conversation_id is None:
        conversations = db_getConversations(user.id)

        return {'status': True, 'conversations': conversations}

    else:
        messages = db_getMessages(user.id, conversation_id)

        return {'status': True, 'messages': messages}






############################################# AUTH #################################################
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
        data={"username": user.username}, expires_delta=recovery_token_exiperes
    )

    return {"recovery_token": recovery_token}


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


@app.get('/test')
async def tests(request: Request):
    #response.set_cookie(key='test', value='200')
    return 200


if __name__ == '__main__':
    uvicorn.run(app)