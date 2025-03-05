from typing import Optional
from pydantic import field_validator,\
    field_serializer, BaseModel, EmailStr, Field, model_serializer
from pydantic_core import PydanticCustomError
from .books import ReturnedBook


__all__ = ["BaseSeller", "IncomingSeller",
            "ReturnedAllSellers", "ReturnedSeller"]

class BaseSeller(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    e_mail: EmailStr = Field(..., max_length=100)
    # password: str = Field(..., max_length=100)

class IncomingSeller(BaseSeller):
    password: str = Field(..., max_length=100)
    #тут мы регистрируем юзера типа




class ReturnedSeller(BaseSeller):
    id: int
    seller_books: list[ReturnedBook] = [] 
    
    @model_serializer
    def hide_password(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "e_mail": self.e_mail,
            "books": self.seller_books 
        }
    

class EditSeller(BaseSeller):
    pass


    
class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]