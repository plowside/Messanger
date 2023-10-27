from pydantic import BaseModel
from typing import Union

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str , None] = None


class User(BaseModel):
    id: int
    username: str
    email: Union[str , None] = None
    first_name: Union[str , None] = None
    last_name: Union[str , None] = None
    disabled: Union[bool , None] = None



class UserInDB(User):
    hashed_password: str


class UserRegister(BaseModel):
    username: str
    first_name: Union[str , None] = None
    last_name: Union[str , None] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class Forgot(BaseModel):
    username: str
    email: Union[str , None] = None
    last_password: Union[str , None] = None