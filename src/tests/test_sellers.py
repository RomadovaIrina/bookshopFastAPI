import pytest
from sqlalchemy import select
from src.auth.auth import hash_password
from src.models.books import Book
from src.models.seller import Seller
from fastapi import status
from icecream import ic
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, Response, status




@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example4.com", 
        password="password123")

    db_session.add(seller)
    await db_session.flush()
    book = Book(
        author="Lermontov", 
        title="Mtziri", 
        pages=510, 
        year=2024, 
        seller_id=seller.id
    )
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/seller/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_seller = await db_session.get(Seller, seller.id)
    assert deleted_seller is None

    all_books = await db_session.execute(select(Book).filter(Book.seller_id == seller.id))
    books = all_books.scalars().all()
    assert len(books) == 0 

    all_sellers = await db_session.execute(select(Seller))
    sellers = all_sellers.scalars().all()
    assert len(sellers) == 0


@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {    
    "first_name": "John",
    "last_name": "Doe",
    "e_mail": "john@example.com",
    "password": "securepassword123"
}
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_seller_id = result_data.pop("id", None)
    assert resp_seller_id, "Seller id not returned from endpoint"

    assert result_data == {    
    "first_name": "John",
    "last_name": "Doe",
    "e_mail": "john@example.com",
    "books": []
}
    

@pytest.mark.asyncio
async def test_create_seller_without_password(async_client):
    data = {    
    "first_name": "John",
    "last_name": "Doe",
    "e_mail": "john@example.com",
}
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):

    seller_1 = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example12.com", 
        password="password123")
    seller_2 = Seller(
        first_name="John_2", 
        last_name="Doe_2", 
        e_mail="john.smith@example13.com", 
        password="password456")
    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/seller/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()["sellers"]) == 2

    assert response.json() == {
        "sellers": [
            {
                "id": seller_1.id,
                "first_name": "John",
                "last_name": "Doe",
                "e_mail": "john.doe@example12.com",
                "books": []
            },
            {
                "id": seller_2.id,
                "first_name": "John_2",
                "last_name": "Doe_2",
                "e_mail": "john.smith@example13.com",
                "books": []
            },
        ]
    }


@pytest.mark.asyncio
async def test_get_seller(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password=hash_password("strongpassword123")
    )
    db_session.add(seller)
    await db_session.flush()
    data = {
        "username": "john.doe@example.com", 
        "password": "strongpassword123"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get(f"/api/v1/seller/{seller.id}", headers = headers)

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "id": seller.id,
        "first_name": "John",
        "last_name": "Doe",
        "e_mail": "john.doe@example.com",
        "books": []
    }



@pytest.mark.asyncio
async def test_edit_seller(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password="password123")

    db_session.add(seller)
    await db_session.commit()

    response = await async_client.put(
        f"/api/v1/seller/{seller.id}",
        json={
            "first_name": "Jonathan",
            "last_name": "Doever",
            "e_mail": "jonathanDoever@example.com",
        }
    )

    assert response.status_code == status.HTTP_200_OK

    updated_seller = await db_session.execute(
        select(Seller).options(selectinload(Seller.seller_books)).filter_by(id=seller.id)
    )
    updated_seller = updated_seller.scalars().first()

    assert updated_seller.first_name == "Jonathan"
    assert updated_seller.last_name == "Doever"
    assert updated_seller.e_mail == "jonathanDoever@example.com"




@pytest.mark.asyncio
async def test_delete_seller_with_invalid_id(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password=hash_password("strongpassword123")
    )
    db_session.add(seller)
    await db_session.flush()
    data = {
        "username": "john.doe@example.com", 
        "password": "strongpassword123"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.delete(f"/api/v1/books/{seller.id + 1}", headers = headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND