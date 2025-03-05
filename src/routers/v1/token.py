
from datetime import timedelta, datetime
from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response, status
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.auth import ACESS_TOKEN_EXPIRE_TIME_MINS, Token, check_password, create_token, oath_bearer, ALGORITHM, JWT_SECRET
from src.configurations import get_async_session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext

from src.models.seller import Seller

DBSession = Annotated[AsyncSession, Depends(get_async_session)]

token_router = APIRouter(tags=["token"], prefix="/token")


async def get_current_seller(
        db_session: DBSession,
        token: str = Depends(oath_bearer), 
        ):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        result = await db_session.execute(select(Seller).filter(Seller.e_mail == email))
        seller = result.scalar_one_or_none()
        if seller is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return seller

@token_router.post("/", response_model=Token)
async def get_token(
    db_session: DBSession,
    data: OAuth2PasswordRequestForm = Depends(), 
    ):
    seller = await db_session.execute(
        select(Seller).filter(Seller.e_mail == data.username)
    )
    seller = seller.scalar_one_or_none()
    if not seller or not check_password(data.password, seller.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACESS_TOKEN_EXPIRE_TIME_MINS)
    access_token = create_token(data={"sub": seller.e_mail}, expire_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


