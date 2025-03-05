# Для импорта из корневого модуля
# import sys
# sys.path.append("..")
# from main import app

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from src.models.books import Book
from src.models.seller import Seller
from src.routers.v1.token import get_current_seller
from src.schemas import IncomingBook, ReturnedAllbooks, ReturnedBook
from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session
from src.schemas.books import UpdateBook

books_router = APIRouter(tags=["books"], prefix="/books")

# CRUD - Create, Read, Update, Delete

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о книге в БД. Возвращает созданную книгу.
# @books_router.post("/books/", status_code=status.HTTP_201_CREATED)
@books_router.post(
    "/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_book(
    book: IncomingBook,
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller),
):  # прописываем модель валидирующую входные данные
    # session = get_async_session() вместо этого мы используем иньекцию зависимостей DBSession

    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    new_book = Book(
        **{
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "pages": book.pages,
            "seller_id": current_seller.id
        }
    )

    session.add(new_book)
    await session.flush()

    return new_book




# Ручка, возвращающая все книги
@books_router.get("/", response_model=ReturnedAllbooks)
async def get_all_books(session: DBSession):
    # Хотим видеть формат
    # books: [{"id": 1, "title": "blabla", ...., "year": 2023},{...}]
    query = select(Book)  # SELECT * FROM book
    result = await session.execute(query)
    books = result.scalars().all()
    return {"books": books}


# Ручка для получения книги по ее ИД
@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_book(book_id: int, session: DBSession):
    if result := await session.get(Book, book_id):
        return result

    return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для удаления книги
@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int, 
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller)
    ):
    deleted_book = await session.get(Book, book_id)

    if not deleted_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    
    if deleted_book.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    await session.delete(deleted_book)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Ручка для обновления данных о книге
@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(
    book_id: int, 
    new_book_data: UpdateBook, 
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller)
    ):

    book = await session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if (book.seller_id != current_seller.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


    book.author = new_book_data.author
    book.title = new_book_data.title
    book.year = new_book_data.year
    book.pages = new_book_data.pages

    book.seller_id = current_seller.id
    await session.commit()

    await session.refresh(book)
    return ReturnedBook(
        id=book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        pages=book.pages,
        seller_id=book.seller_id
    )