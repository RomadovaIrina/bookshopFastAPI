import time
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
import jwt
from passlib.context import CryptContext

from datetime import datetime, timedelta

from pydantic import BaseModel

ACESS_TOKEN_EXPIRE_TIME_MINS = 60 * 24 #через сутки токен прератится в тыкву


JWT_SECRET = "my_secret_key_123123123" #я не супер поняла каким он должен быть,     
                                       #но хотя бы какой то
ALGORITHM = "HS256"

# шифруем 
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

oath_bearer = OAuth2PasswordBearer(tokenUrl="api/v1/token")

class Token(BaseModel):
    access_token: str
    token_type: str


def create_token(data: dict, expire_delta: timedelta):
    expires = expire_delta + datetime.utcnow() 
    to_encode = data.copy()
    to_encode.update({'exp': expires})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def hash_password(password: str):
    return bcrypt_context.hash(password)

def check_password(password: str, hashed_password: str):
    return bcrypt_context.verify(password, hashed_password)

