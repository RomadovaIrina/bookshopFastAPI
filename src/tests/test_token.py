from httpx import AsyncClient
import pytest
from fastapi import HTTPException, status
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.auth.auth import hash_password
from src.models.seller import Seller
from src.routers.v1.token import (
    JWT_SECRET,
    ALGORITHM,
    ACESS_TOKEN_EXPIRE_TIME_MINS,
    check_password
)
from src.routers.v1.token import get_current_seller


#Эти тесты я писала самыми последними,
#  где я уже +- разобралась с этой чудо гадостью
@pytest.fixture
async def seller(db_session):
    seller = Seller(
        first_name="John",
        last_name="Doe",
        e_mail="john.doe@example.com",  
        password=hash_password("password123")  
    )
    db_session.add(seller)
    await db_session.flush()  
    return seller



@pytest.mark.asyncio
async def test_get_current_seller_invalid_token(db_session):
    expired_token = jwt.encode(
        {"sub": "test@example.com", "exp": datetime.utcnow() - timedelta(minutes=5)},
        JWT_SECRET,
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=expired_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
 
    invalid_token = jwt.encode(
        {"sub": "test@example.com"},
        "wrong_secret",
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=invalid_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_password_hashing():
    password = "securepassword123"
    hashed = hash_password(password)
    
    assert isinstance(hashed, str)
    assert hashed != password
    assert check_password(password, hashed)
    assert not check_password("wrong_password", hashed)


@pytest.mark.asyncio
async def test_get_current_seller_missing_subject(db_session):
    invalid_token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(minutes=5)},
        JWT_SECRET,
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=invalid_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_token_with_invalid_signature(async_client: AsyncClient):
    invalid_token = jwt.encode(
        {"sub": "fake@user.com", "exp": datetime.utcnow() + timedelta(minutes=30)},
        "wrong_secret_key",
        algorithm=ALGORITHM
    )
    
    response = await async_client.get(
        "/api/v1/seller/1",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED