from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from src.auth.auth import hash_password
from src.models.seller import Seller
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session
from src.routers.v1.token import get_current_seller
from src.schemas.seller import EditSeller, ReturnedSeller, IncomingSeller,\
    ReturnedAllSellers


seller_router = APIRouter(tags=["seller"], prefix="/seller")


DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о продавце в БД.
@seller_router.post("/", response_model=ReturnedSeller,
                    status_code=status.HTTP_201_CREATED)  
async def register_seller(
    seller_data: IncomingSeller,
    session: DBSession
):
    
    new_seller = Seller(
    first_name=seller_data.first_name,
    last_name=seller_data.last_name,
    e_mail=seller_data.e_mail,
    password=hash_password(seller_data.password)
    )

    session.add(new_seller)
    await session.flush()

    return ReturnedSeller(
        id=new_seller.id,
        first_name=new_seller.first_name,
        last_name=new_seller.last_name,
        e_mail=new_seller.e_mail,
        books=[]
    )


# Получаем всех пользователей
@seller_router.get("/", response_model = ReturnedAllSellers)
async def get_sellers(session: DBSession):
    query = select(Seller).options(selectinload(Seller.seller_books))
    result = await session.execute(query)
    sellers = result.scalars().all()
    return {"sellers": sellers}






@seller_router.get("/{seller_id}", response_model=ReturnedSeller)
async def get_seller(
    seller_id: int, 
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller)
    ):
    if current_seller.id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await session.execute(
        select(Seller)
        .options(selectinload(Seller.seller_books))
        .filter(Seller.id == seller_id) 
    )
    seller = result.scalar_one_or_none() 
    if seller:
        return ReturnedSeller(
            id=seller.id,
            first_name=seller.first_name,
            last_name=seller.last_name,
            e_mail=seller.e_mail,
            books=seller.seller_books
        )
    return Response(status_code=status.HTTP_404_NOT_FOUND)


# Обновляем дааные продавца
@seller_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(
    seller_id: int,
    seller_data: EditSeller,
    session: DBSession
):
    query = select(Seller).filter(Seller.id == seller_id)
    result = await session.execute(
        select(Seller)
        .options(selectinload(Seller.seller_books))
        .where(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    
    if seller_data.first_name:
        seller.first_name = seller_data.first_name
    if seller_data.last_name:
        seller.last_name = seller_data.last_name
    if seller_data.e_mail:
        seller.e_mail = seller_data.e_mail
    

    await session.commit()

    await session.refresh(seller)
    return ReturnedSeller(
        id=seller.id,
        first_name=seller.first_name,
        last_name=seller.last_name,
        e_mail=seller.e_mail,
        books=seller.seller_books 
    )



# Удаляем продавца => еще и его книги
@seller_router.delete("/{seller_id}",)
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await session.get(Seller, seller_id)
    if not deleted_seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await session.delete(deleted_seller)
    await session.commit() 
    return Response(status_code=status.HTTP_204_NO_CONTENT)


