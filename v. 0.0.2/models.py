from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int | None = None
    username: str | None = None


class User(BaseModel):
    id: int
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    registration_date: int | None = None
    access_type: int | None = None



class UserInDB(User):
    id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None
    hashed_password: str
    registration_date: int
    access_type: int


class UserRegister(BaseModel):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class Forgot(BaseModel):
    id: int | None = None
    username: str | None = None
    email: str | None = None
    last_password: str | None = None

class Reset(BaseModel):
    recovery_token: str
    password: str | None = None
    password_check: str | None = None
    logout: str | None = False