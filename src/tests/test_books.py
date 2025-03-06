import pytest
from sqlalchemy import select
from src.auth.auth import hash_password
from src.models.books import Book
from fastapi import status
from icecream import ic
from fastapi import APIRouter, Depends, HTTPException, Response, status
from src.models.seller import Seller


# Фикстура для очистки базы данных
@pytest.fixture(autouse=True)
async def cleanup_db(db_session):
    yield
    await db_session.execute('DELETE FROM books_table')
    await db_session.execute('DELETE FROM sellers_table')
    await db_session.commit()


@pytest.mark.asyncio
async def test_delete_book(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doee@example.com", 
        password=hash_password("strongpassword123")
    )
    db_session.add(seller)
    await db_session.flush()

    # Получаем токен для авторизации
    data = {
        "username": "john.doee@example.com", 
        "password": "strongpassword123"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.commit()

    response = await async_client.delete(f"/api/v1/books/{book.id}", headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_book = await db_session.get(Book, book.id)
    assert deleted_book is None

    await db_session.commit()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio
async def test_create_book(async_client, db_session):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password=hash_password("strongpassword123"))
    db_session.add(seller)
    await db_session.flush()
    data = {
        "username": "john.doe@example.com", 
        "password": "strongpassword123"    
    }
    token_response = await async_client.post("/api/v1/token/", data=data) 
    token = token_response.json().get("access_token")
    book_data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post("/api/v1/books/", json=book_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    result_data = response.json()
    resp_book_id = result_data.pop("id", None)
    assert resp_book_id, "Book id not returned from endpoint"
    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": seller.id
    }



@pytest.mark.asyncio
async def test_create_book_with_old_year(db_session,async_client):
    
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password=hash_password("strongpassword123"))
    db_session.add(seller)
    await db_session.flush()
    data = {
        "username": "john.doe@example.com", 
        "password": "strongpassword123"    
    }
    token_response = await async_client.post("/api/v1/token/", data=data) 
    token = token_response.json().get("access_token")

    headers = {"Authorization": f"Bearer {token}"}
    book_data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": seller.id
    }
    response = await async_client.post("/api/v1/books/", json=book_data, headers = headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio
async def test_get_books(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", e_mail="john.doe@example.com", password="password123")
    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/books/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["books"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2001,
                "id": book.id,
                "pages": 104,
                "seller_id": seller.id
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 1997,
                "id": book_2.id,
                "pages": 104,
                "seller_id": seller.id
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio
async def test_get_single_book(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", e_mail="john.doe@example.com", password="password123")
    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": seller.id
    }


# Тест на ручку обновления книги
@pytest.mark.asyncio
async def test_update_book(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe@example.com", 
        password=hash_password("strongpassword123")
    )
    db_session.add(seller)
    await db_session.flush()

    # Получаем токен для авторизации
    data = {
        "username": "john.doe@example.com", 
        "password": "strongpassword123"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104,seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/books/{book.id}",
        json={
            "title": "Mziri",
            "author": "Lermontov",
            "pages": 100,
            "year": 2007,
            "id": book.id,
            "seller_id": seller.id
        }, headers = headers
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 100
    assert res.year == 2007
    assert res.id == book.id
    assert res.seller_id == seller.id





@pytest.mark.asyncio
async def test_delete_book_with_invalid_book_id(db_session, async_client):
    seller = Seller(
        first_name="John", 
        last_name="Doe", 
        e_mail="john.doe2@example.com", 
        password=hash_password("strongpassword123")
    )
    db_session.add(seller)
    await db_session.flush()

    # Получаем токен для авторизации
    data = {
        "username": "john.doe2@example.com", 
        "password": "strongpassword123"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}


    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/books/{book.id + 1}", headers = headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
