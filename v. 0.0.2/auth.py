import time

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Annotated

from models import *#UserInDB, UserRegister, TokenData, User

from dbApi import *


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "317aef2b141c92168b99303376221476e9130e9dff7e8ad27b00c95dd85ad00d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180



def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(user_id: int = None, username: str = None):
    user_db = db_get_user(user_id, username)
    if user_db:
        return UserInDB(**user_db)


def reg_user(user: UserRegister):
    user.first_name = user.first_name if user.first_name != '' else None
    user.last_name = user.last_name if user.last_name != '' else None

    user_id = db_create_user(user.username, user.first_name, user.last_name, get_password_hash(user.password))

    return get_user(user_id)



def authenticate_user(username: str, password: str):
    user = get_user(username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_jwt_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )):
    

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_None(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except:
        return None
    user = get_user(username=token_data.username)
    if user is None:
        return None
    return user


async def reset_user(recovery_token: str, password: str):
    try:
        payload = jwt.decode(recovery_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return {'status': False}
        token_data = TokenData(id=user_id)
    except:
        return {'status': False}
    

    return {'status': True, 'user': UserInDB(**db_update_user(user_id=token_data.id, hashed_password=get_password_hash(password)))}